"""HTTP surface (FastAPI). Thin transport layer over the engine."""

from __future__ import annotations

import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Annotated

from fastapi import Depends, FastAPI, HTTPException, Query, Request

from omnisource import __version__
from omnisource.cache import InMemoryCache, RedisCache
from omnisource.cache.base import CacheBackend
from omnisource.core.config import Settings, get_settings
from omnisource.core.engine import OmniSourceEngine
from omnisource.core.exceptions import ConfigurationError, ProviderError
from omnisource.core.models import AggregatedResponse, HealthReport, ProviderMetadata
from omnisource.providers import ArchiveProvider, CatalogProvider, NewsProvider, ProviderRegistry

logger = logging.getLogger(__name__)


def build_cache(settings: Settings) -> CacheBackend:
    """Pick a cache backend; fall back to in-memory when Redis is disabled."""
    if not settings.cache_enabled:
        return InMemoryCache(default_ttl=0)
    try:
        return RedisCache(settings.redis_url, default_ttl=settings.cache_ttl)
    except Exception as exc:  # pragma: no cover
        logger.warning("redis unavailable (%s); using in-memory cache", exc)
        return InMemoryCache(default_ttl=settings.cache_ttl)


def build_engine(settings: Settings | None = None) -> OmniSourceEngine:
    """Compose the default engine: sample providers + configured cache."""
    settings = settings or get_settings()
    registry = ProviderRegistry([NewsProvider(), CatalogProvider(), ArchiveProvider(seed=7)])
    return OmniSourceEngine(registry, cache=build_cache(settings), settings=settings)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    app.state.engine = build_engine()
    logger.info("engine ready providers=%s", app.state.engine.registry.names)
    try:
        yield
    finally:
        await app.state.engine.close()


def get_engine(request: Request) -> OmniSourceEngine:
    return request.app.state.engine  # type: ignore[no-any-return]


EngineDep = Annotated[OmniSourceEngine, Depends(get_engine)]


def create_app() -> FastAPI:
    """Application factory."""
    app = FastAPI(
        title="OmniSource",
        version=__version__,
        summary="Resilient multi-source aggregation API",
        lifespan=lifespan,
    )

    @app.get("/health", tags=["ops"])
    async def health(engine: EngineDep) -> dict[str, object]:
        reports = await engine.health_check()
        return {
            "status": "ok",
            "version": __version__,
            "cache": await engine.cache.ping(),
            "providers": [r.model_dump(mode="json") for r in reports],
        }

    @app.get("/providers", tags=["providers"])
    async def list_providers(engine: EngineDep) -> dict[str, list[str]]:
        return {"providers": engine.registry.names}

    @app.get("/providers/health", response_model=list[HealthReport], tags=["providers"])
    async def providers_health(engine: EngineDep) -> list[HealthReport]:
        return await engine.health_check()

    @app.get("/search", response_model=AggregatedResponse, tags=["search"])
    async def search(
        engine: EngineDep,
        q: Annotated[str, Query(min_length=1, max_length=256, description="Search query")],
        providers: Annotated[
            list[str] | None, Query(description="Restrict to these providers")
        ] = None,
        limit: Annotated[int, Query(ge=1, le=500)] = 25,
        timeout: Annotated[float | None, Query(gt=0, le=30)] = None,
        use_cache: Annotated[bool, Query()] = True,
    ) -> AggregatedResponse:
        try:
            return await engine.search(
                q, providers=providers, limit=limit, timeout=timeout, use_cache=use_cache
            )
        except ConfigurationError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    @app.get(
        "/providers/{provider}/items/{item_id}",
        response_model=ProviderMetadata,
        tags=["providers"],
    )
    async def metadata(engine: EngineDep, provider: str, item_id: str) -> ProviderMetadata:
        try:
            return await engine.get_metadata(provider, item_id)
        except ConfigurationError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        except ProviderError as exc:
            raise HTTPException(status_code=502, detail=str(exc)) from exc

    return app


app = create_app()
