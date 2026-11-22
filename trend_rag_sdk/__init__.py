"""
Trend RAG SDK
Python client for 20,000+ Tech Trends and Factchecks Database.
"""

from .client import TrendRAGClient, TrendItem
from .factcheck import FactcheckEngine, FourPillarEvidenceHarvester, estimate_tokens

__version__ = "2.1.0"
__all__ = [
    "TrendRAGClient",
    "TrendItem",
    "FactcheckEngine",
    "FourPillarEvidenceHarvester",
    "estimate_tokens",
    "__version__"
]
