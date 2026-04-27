"""核心資料模型。"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime

from ..format.alarm_log import Event
from ..format.data_log import Sample
from ..format.tag_cfg import Channel


@dataclass(frozen=True)
class ResampleOptions:
    interval_seconds: int = 120
    start: datetime | None = None
    end: datetime | None = None
    selected_channels: list[int] = field(default_factory=list)
    show_blanks: bool = True


@dataclass(frozen=True)
class ResampledRow:
    timestamp: datetime
    values: list[str]


@dataclass(frozen=True)
class RecorderData:
    channels: list[Channel]
    samples: dict[int, list[Sample]]
    events: list[Event]
