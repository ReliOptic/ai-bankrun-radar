"""Data Quality Gate with circuit breaker.

Assesses data freshness and completeness, assigns DataStatus,
and computes score discount factors. Circuit breaker opens after
consecutive failures, marking source OFFLINE.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from contagion_radar.core.config import QualityGateConfig, SourceQualityConfig
from contagion_radar.core.types import DataConfidence, DataStatus


class DataQualityGate:
    """Evaluates data quality and manages circuit breaker state per source."""

    def __init__(self, config: QualityGateConfig):
        self._config = config
        self._failure_counts: dict[str, int] = {}
        self._last_success: dict[str, datetime] = {}

    def assess(
        self,
        source: str,
        data: dict[str, Any],
        fetch_time: datetime,
        error: bool = False,
    ) -> DataConfidence:
        """Evaluate data quality and return a DataConfidence assessment.

        Args:
            source: adapter source name (e.g., "defillama")
            data: the fetched data dict (empty if error)
            fetch_time: when the fetch completed
            error: True if the fetch raised an exception
        """
        source_config = self._config.sources.get(source)
        if source_config is None:
            source_config = SourceQualityConfig(
                max_stale_seconds=900,
                circuit_breaker_failures=3,
            )

        if error:
            self._failure_counts[source] = self._failure_counts.get(source, 0) + 1
        else:
            self._failure_counts[source] = 0
            self._last_success[source] = fetch_time

        consecutive_failures = self._failure_counts.get(source, 0)

        # Circuit breaker: too many consecutive failures → OFFLINE
        if consecutive_failures >= source_config.circuit_breaker_failures:
            return DataConfidence(
                source=source,
                status=DataStatus.OFFLINE,
                staleness_seconds=self._staleness(source, fetch_time),
                completeness_ratio=0.0,
                consecutive_failures=consecutive_failures,
                last_successful_fetch=self._last_success.get(source),
            )

        # Error but not yet tripped circuit breaker → DEGRADED
        if error:
            return DataConfidence(
                source=source,
                status=DataStatus.DEGRADED,
                staleness_seconds=self._staleness(source, fetch_time),
                completeness_ratio=0.0,
                consecutive_failures=consecutive_failures,
                last_successful_fetch=self._last_success.get(source),
            )

        # Check staleness
        staleness = self._staleness(source, fetch_time)
        if staleness > source_config.max_stale_seconds:
            status = DataStatus.STALE
        else:
            status = DataStatus.FRESH

        # Check completeness
        completeness = self._check_completeness(data, source_config)
        if completeness < 1.0:
            status = DataStatus.DEGRADED

        return DataConfidence(
            source=source,
            status=status,
            staleness_seconds=staleness,
            completeness_ratio=completeness,
            consecutive_failures=consecutive_failures,
            last_successful_fetch=self._last_success.get(source),
        )

    def score_discount(self, confidence: DataConfidence) -> float:
        """Map DataStatus to a score multiplier.

        FRESH→1.0, STALE→0.7, DEGRADED→0.4, OFFLINE→0.0
        """
        return self._config.score_discounts.get(confidence.status.value, 0.0)

    def reset(self, source: str) -> None:
        """Reset circuit breaker for a source."""
        self._failure_counts.pop(source, None)

    def _staleness(self, source: str, now: datetime) -> float:
        last = self._last_success.get(source)
        if last is None:
            return 0.0
        return (now - last).total_seconds()

    def _check_completeness(self, data: dict[str, Any], config: SourceQualityConfig) -> float:
        if not config.completeness_required_fields:
            return 1.0
        present = sum(
            1 for field in config.completeness_required_fields
            if data.get(field) is not None
        )
        return present / len(config.completeness_required_fields)
