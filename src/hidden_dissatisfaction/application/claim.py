"""Claim command port for the P9 Specialist workflow."""

from dataclasses import dataclass
from typing import Protocol
from uuid import UUID


@dataclass(frozen=True)
class ClaimResult:
    """The refreshed workload values after a successful claim."""

    order_id: str
    active_count: int
    capacity: int


class ClaimCase(Protocol):
    """Atomically claim a pending case for the authenticated Specialist."""

    def execute(self, order_id: str, actor_id: UUID) -> ClaimResult: ...
