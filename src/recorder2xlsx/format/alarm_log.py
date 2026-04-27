"""Alarm.lst 事件記錄解析。"""
from __future__ import annotations

import struct
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path

from .errors import RecorderFormatError

# Windows FILETIME 的起點（UTC）
FILETIME_EPOCH = datetime(1601, 1, 1, tzinfo=timezone.utc)

# action_type 對應中文動作名稱
_ACTION_NAMES: dict[int, str] = {
    0x06: "開機",
    0x07: "更新",
    0x0F: "卸載",
    0x10: "開機",
}

HEADER_SIZE = 20
FT_OFFSET = 8       # record 內 FILETIME 的偏移
ACTION_OFFSET = 3   # record 內 action_type 的偏移


@dataclass(frozen=True)
class Event:
    """單筆警報事件記錄。"""

    action: str
    source: str
    occurred_at: datetime
    cleared_at: datetime | None
    value: str
    acknowledged: bool


def parse_alarm_log(path: Path) -> list[Event]:
    """解析 Alarm.lst 二進位檔案，回傳事件列表。

    Args:
        path: Alarm.lst 檔案路徑。

    Returns:
        解析後的 Event 列表。

    Raises:
        RecorderFormatError: 檔案不存在時引發。
    """
    if not path.is_file():
        raise RecorderFormatError(f"找不到 {path}")

    data = path.read_bytes()
    if len(data) < HEADER_SIZE:
        return []

    record_size = struct.unpack_from('<H', data, 6)[0]
    record_count = struct.unpack_from('<H', data, 8)[0]

    if record_size == 0:
        return []

    events: list[Event] = []
    for i in range(record_count):
        off = HEADER_SIZE + i * record_size
        if off + record_size > len(data):
            break
        events.append(_parse_record(data[off:off + record_size]))
    return events


def _parse_record(rec: bytes) -> Event:
    """解析單筆 304 bytes 記錄。"""
    action_code = rec[ACTION_OFFSET]
    action = _ACTION_NAMES.get(action_code, f"未知({action_code:#04x})")

    # 將 Windows FILETIME（100ns ticks since 1601-01-01 UTC）轉換為 naive datetime（截斷到秒）
    ft = struct.unpack_from('<Q', rec, FT_OFFSET)[0]
    td = timedelta(microseconds=ft // 10)
    occurred_at = (FILETIME_EPOCH + td).replace(tzinfo=None, microsecond=0)

    return Event(
        action=action,
        source="",
        occurred_at=occurred_at,
        cleared_at=None,
        value="",
        acknowledged=False,
    )
