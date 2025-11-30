from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import Enum


class OutageType(Enum):
    """Enum for the type of outage."""

    PLANNED = "unpl"
    UNPLANNED = "awarie"


@dataclass
class Outage:
    """Represents a power outage from Enea Operator."""

    region: str
    description: str
    start_time: datetime | None
    end_time: datetime | None
