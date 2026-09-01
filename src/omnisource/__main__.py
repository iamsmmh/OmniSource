"""``python -m omnisource`` — run the API with uvicorn."""

from __future__ import annotations

import uvicorn

from omnisource.core.config import get_settings


def main() -> None:
    settings = get_settings()
    uvicorn.run(
        "omnisource.api.app:app",
        host=settings.host,
        port=settings.port,
        log_level=settings.log_level.lower(),
    )


if __name__ == "__main__":  # pragma: no cover
    main()
