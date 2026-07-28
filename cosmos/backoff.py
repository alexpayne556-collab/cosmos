"""
Unified backoff utility (ADR-026 / Drill 2 + Drill 3).

Exponential backoff with FULL jitter and named profile presets. Full jitter
(AWS "Exponential Backoff and Jitter"): the actual delay is U(0, ceiling),
which decorrelates retries across many clients hitting the same endpoint.

Two ratified schedules differ on purpose:
    SEC_EDGAR_PROFILE : 30s -> 2m -> 10m   (Drill 3, SEC fair-access)
    SHEETS_PROFILE    : 30s -> 2m -> 8m    (Drill 2, Sheet unreachable)

`compute_delay` and `retry` accept an injectable rng/sleep so the policy is
fully deterministic under test.
"""
from __future__ import annotations

import random
import time
from dataclasses import dataclass
from typing import Callable, Iterator, Optional, Sequence, Tuple, Type


@dataclass(frozen=True)
class BackoffProfile:
    name: str
    base_delays: Tuple[float, ...]   # per-attempt ceilings, seconds
    max_attempts: int
    jitter: str = "full"             # 'full' | 'none'

    def ceiling(self, attempt: int) -> float:
        """Nominal ceiling for a 1-based attempt; clamps to the last defined step."""
        if attempt < 1:
            raise ValueError("attempt is 1-based")
        idx = min(attempt, len(self.base_delays)) - 1
        return self.base_delays[idx]


SEC_EDGAR_PROFILE = BackoffProfile("sec_edgar", (30.0, 120.0, 600.0), max_attempts=3)
SHEETS_PROFILE = BackoffProfile("sheets", (30.0, 120.0, 480.0), max_attempts=3)

PROFILES = {p.name: p for p in (SEC_EDGAR_PROFILE, SHEETS_PROFILE)}


def compute_delay(profile: BackoffProfile, attempt: int,
                  rng: Optional[random.Random] = None) -> float:
    """Return the (possibly jittered) delay for a 1-based attempt."""
    ceiling = profile.ceiling(attempt)
    if profile.jitter == "full":
        r = rng if rng is not None else random
        return r.uniform(0.0, ceiling)          # full jitter: U(0, ceiling)
    if profile.jitter == "none":
        return ceiling
    raise ValueError(f"unknown jitter mode {profile.jitter!r}")


def delays(profile: BackoffProfile,
           rng: Optional[random.Random] = None) -> Iterator[float]:
    for attempt in range(1, profile.max_attempts + 1):
        yield compute_delay(profile, attempt, rng=rng)


class RetryExhausted(Exception):
    def __init__(self, profile: BackoffProfile, last_exc: Optional[BaseException]):
        super().__init__(
            f"retries exhausted for profile {profile.name!r} "
            f"after {profile.max_attempts} attempts"
        )
        self.profile = profile
        self.last_exc = last_exc


def retry(func: Callable[[], object],
          profile: BackoffProfile,
          *,
          retry_on: Sequence[Type[BaseException]] = (Exception,),
          sleep: Callable[[float], None] = time.sleep,
          rng: Optional[random.Random] = None,
          on_retry: Optional[Callable[[int, float, BaseException], None]] = None):
    """Call `func` with exponential-backoff retries. Sleeps between attempts,
    never after the final one. Raises RetryExhausted carrying the last error."""
    last: Optional[BaseException] = None
    for attempt in range(1, profile.max_attempts + 1):
        try:
            return func()
        except tuple(retry_on) as exc:
            last = exc
            if attempt >= profile.max_attempts:
                break
            delay = compute_delay(profile, attempt, rng=rng)
            if on_retry is not None:
                on_retry(attempt, delay, exc)
            sleep(delay)
    raise RetryExhausted(profile, last)
