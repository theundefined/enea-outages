from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass
class Outage:
    """Represents a power outage from Enea Operator."""

    region: str
    description: str
    end_time: datetime
