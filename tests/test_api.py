"""API contract tests using FastAPI's TestClient."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from omnisource.api.app import create_app


@pytest.fixture(scope="module")
def client() -> TestClient:
    with TestClient(create_app()) as test_client:
        yield test_client


def test_health(client: TestClient) -> None:
    response = client.get("/health")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert {p["provider"] for p in body["providers"]} == {"news", "catalog", "archive"}


def test_list_providers(client: TestClient) -> None:
    assert client.get("/providers").json() == {"providers": ["news", "catalog", "archive"]}


def test_search_returns_standard_schema(client: TestClient) -> None:
    body = client.get("/search", params={"q": "python", "limit": 5}).json()
    assert body["query"] == "python"
    assert body["total"] <= 5
    assert {"items", "results", "elapsed_ms", "generated_at"} <= body.keys()


def test_search_provider_filter(client: TestClient) -> None:
    body = client.get("/search", params={"q": "x", "providers": ["news"]}).json()
    assert {r["provider"] for r in body["results"]} == {"news"}


def test_search_unknown_provider_is_400(client: TestClient) -> None:
    assert client.get("/search", params={"q": "x", "providers": ["ghost"]}).status_code == 400


def test_search_requires_query(client: TestClient) -> None:
    assert client.get("/search").status_code == 422


def test_metadata_endpoint(client: TestClient) -> None:
    body = client.get("/providers/news/items/abc").json()
    assert body == {
        "id": "abc",
        "provider": "news",
        "title": "news entity abc",
        "fields": {"source": "news", "latency": 0.05},
    }


def test_metadata_unknown_provider_is_404(client: TestClient) -> None:
    assert client.get("/providers/ghost/items/1").status_code == 404


def test_degraded_flag_is_serialized(client: TestClient) -> None:
    body = client.get("/search", params={"q": "deadline", "timeout": 0.001}).json()
    assert body["degraded"] is True
    assert body["total"] == 0
