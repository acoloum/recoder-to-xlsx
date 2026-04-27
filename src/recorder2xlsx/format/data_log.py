"""Pn.dat + Pn.idx 通道資料解析（1 sample/秒）。"""
from __future__ import annotations

import struct
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path

from .errors import RecorderFormatError

# Windows FILETIME 基準點（UTC 1601-01-01）
FILETIME_EPOCH = datetime(1601, 1, 1, tzinfo=timezone.utc)
# idx 標頭大小（bytes）
IDX_HEADER_SIZE = 64
# idx 後續每筆 entry 大小（bytes）
IDX_ENTRY_SIZE = 32
# 斷線標記值
DISCONNECT = 0x7FFF


@dataclass(frozen=True)
class Sample:
    """單一採樣點。"""

    timestamp: datetime  # naive UTC datetime，含 microsecond（繼承自 FILETIME）
    value: float         # 斷線時為 0.0
    status: str          # "ok" 或 "斷線"（或其他錯誤字串）


def parse_day(day_dir: Path, channel: int) -> list[Sample]:
    """解析指定日期目錄中單一通道的全部 samples。

    Args:
        day_dir: 包含 Pn.dat / Pn.idx 的目錄（例如 .../DataLog/20260424）。
        channel: 通道編號，對應檔名 P{channel}.dat / P{channel}.idx。

    Returns:
        依時間順序排列的 Sample 清單。

    Raises:
        RecorderFormatError: 找不到 idx 或 dat 檔案時。
    """
    idx_path = day_dir / f"P{channel}.idx"
    dat_path = day_dir / f"P{channel}.dat"
    if not idx_path.is_file() or not dat_path.is_file():
        raise RecorderFormatError(f"找不到 {idx_path} 或 {dat_path}")

    idx = idx_path.read_bytes()
    dat = dat_path.read_bytes()

    # idx 檔案至少需有 header（64 bytes）
    if len(idx) < IDX_HEADER_SIZE:
        return []

    samples: list[Sample] = []

    # 收集所有 entries：header 首筆（offset 0x20）+ 後續 entries（offset 0x40+）
    entries: list[tuple[int, int, int]] = []  # (filetime, dat_byte_offset, count)

    # ── Header 首筆 entry ──
    ft = struct.unpack_from("<Q", idx, 0x20)[0]
    dat_off = struct.unpack_from("<I", idx, 0x28)[0]
    count = struct.unpack_from("<I", idx, 0x2C)[0]
    if ft and count:
        entries.append((ft, dat_off, count))

    # ── 後續 entries（每筆 32 bytes，從 offset 0x40 開始）──
    entry_off = IDX_HEADER_SIZE
    while entry_off + IDX_ENTRY_SIZE <= len(idx):
        ft = struct.unpack_from("<Q", idx, entry_off)[0]
        dat_off = struct.unpack_from("<I", idx, entry_off + 8)[0]
        count = struct.unpack_from("<I", idx, entry_off + 12)[0]
        if ft and count:
            entries.append((ft, dat_off, count))
        entry_off += IDX_ENTRY_SIZE

    ONE_SECOND = timedelta(seconds=1)

    # ── 依每個 entry 解析對應 dat 資料 ──
    for ft, dat_off, count in entries:
        # 限制不超出 dat 邊界
        available = (len(dat) - dat_off) // 2
        n = min(count, available)
        if n <= 0:
            continue
        t0 = _ft_to_dt(ft)
        # 批次解包整個 entry 的所有 raw 值，避免逐筆呼叫 struct.unpack_from
        raws = struct.unpack_from(f"<{n}H", dat, dat_off)
        ts = t0
        for raw in raws:
            if raw == DISCONNECT:
                samples.append(Sample(timestamp=ts, value=0.0, status="斷線"))
            else:
                samples.append(Sample(timestamp=ts, value=raw / 10.0, status="ok"))
            ts += ONE_SECOND

    return samples


def _ft_to_dt(ft: int) -> datetime:
    """將 Windows FILETIME（100-nanosecond intervals since 1601-01-01 UTC）
    轉換為 naive UTC datetime，保留 microsecond 精度。
    """
    td = timedelta(microseconds=ft // 10)
    return (FILETIME_EPOCH + td).replace(tzinfo=None)
