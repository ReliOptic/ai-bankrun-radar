"""Base data adapter interface.

All adapters return (data, DataConfidence) tuples.
Each adapter handles its own HTTP calls and response parsing.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any

from contagion_radar.core.types import DataConfidence, DataStatus


class DataAdapter(ABC):
    """Abstract base for all data source adapters."""

    source_name: str = "unknown"

    @abstractmethod
    async def fetch(self, entity: str, **kwargs: Any) -> tuple[dict[str, Any], DataConfidence]:
        """Fetch data for an entity. Returns (data_dict, confidence)."""

    def _make_confidence(
        self,
        status: DataStatus = DataStatus.FRESH,
        staleness: float = 0.0,
        completeness: float = 1.0,
        consecutive_failures: int = 0,
    ) -> DataConfidence:
        return DataConfidence(
            source=self.source_name,
            status=status,
            staleness_seconds=staleness,
            completeness_ratio=completeness,
            consecutive_failures=consecutive_failures,
            last_successful_fetch=datetime.utcnow(),
        )


class AdapterError(Exception):
    """Raised when an adapter fails to fetch data."""

    def __init__(self, source: str, message: str):
        self.source = source
        super().__init__(f"[{source}] {message}")
