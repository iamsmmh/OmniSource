"""OmniSource — a resilient, async multi-source aggregation engine."""

from omnisource.core.engine import OmniSourceEngine
from omnisource.core.models import AggregatedResponse, SearchItem
from omnisource.providers.base import BaseProvider

__version__ = "0.1.0"
__all__ = ["AggregatedResponse", "BaseProvider", "OmniSourceEngine", "SearchItem", "__version__"]
