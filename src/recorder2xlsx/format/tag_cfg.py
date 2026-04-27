"""TagCfg.bin 通道設定解析。"""
from __future__ import annotations

import struct
from dataclasses import dataclass
from pathlib import Path

from .errors import RecorderFormatError

CH0_OFFSET = 0xDE56      # 第 0 通道 record 起始 offset
STRIDE = 0x568           # 每通道 stride（1384 bytes）
CHANNEL_COUNT = 18

NAME_OFFSET = 0x000
NAME_MAX = 64
RANGE_LOW_OFFSET = 0x082   # f64 LE
RANGE_HIGH_OFFSET = 0x08A  # f64 LE
UNIT_OFFSET = 0x2DE
UNIT_MAX = 64


@dataclass(frozen=True)
class Channel:
    name: str
    unit: str
    range_low: float
    range_high: float


def parse_tag_cfg(path: Path) -> list[Channel]:
    if not path.is_file():
        raise RecorderFormatError(f"找不到 {path}")
    data = path.read_bytes()
    channels: list[Channel] = []
    for i in range(CHANNEL_COUNT):
        off = CH0_OFFSET + i * STRIDE
        rec = data[off:off + STRIDE]
        if len(rec) < STRIDE:
            raise RecorderFormatError(f"TagCfg.bin 第 {i} 通道資料不完整（檔案過短）")
        name = _read_utf16z(rec, NAME_OFFSET, NAME_MAX)
        unit = _read_utf16z(rec, UNIT_OFFSET, UNIT_MAX)
        range_low = struct.unpack_from('<d', rec, RANGE_LOW_OFFSET)[0]
        range_high = struct.unpack_from('<d', rec, RANGE_HIGH_OFFSET)[0]
        channels.append(Channel(name=name, unit=unit, range_low=range_low, range_high=range_high))
    return channels


def _read_utf16z(buf: bytes, offset: int, max_bytes: int) -> str:
    """讀 UTF-16-LE null-terminated 字串。"""
    raw = buf[offset:offset + max_bytes]
    for i in range(0, len(raw) - 1, 2):
        if raw[i] == 0 and raw[i + 1] == 0:
            raw = raw[:i]
            break
    return raw.decode('utf-16-le', errors='replace')
