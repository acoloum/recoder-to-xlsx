"""Phase C 驗收：5 個 parser 串接後能還原範例 Pen CSV。

CSV 格式：
  Row 0: 欄位名稱（日期,時間,AI1..AI18）
  Row 1: 量測方式（瞬間值 ×18）
  Row 2: 工程單位（°C ×18）
  Row 3+: 資料（120 秒間隔；AI 斷線 → "錯誤"）
"""
import csv
from datetime import datetime
from pathlib import Path

import pytest

from recorder2xlsx.format.data_log import Sample, parse_day


# ── 輔助 ────────────────────────────────────────────────────────────────────


def _parse_csv_timestamp(date_str: str, time_str: str) -> datetime:
    """將 "04/24/2026" + "15:47:14:183" 轉為 datetime（microsecond=毫秒×1000）。"""
    dt = datetime.strptime(date_str, "%m/%d/%Y")
    h, m, s, ms = time_str.split(":")
    return dt.replace(
        hour=int(h), minute=int(m), second=int(s), microsecond=int(ms) * 1000
    )


def _read_expected_csv(csv_path: Path) -> list[tuple[datetime, list[str]]]:
    """讀 Pen CSV，跳過 3 個標題行，回傳 (timestamp, [AI1..AI18]) 清單。"""
    rows: list[tuple[datetime, list[str]]] = []
    with csv_path.open("r", encoding="big5") as f:
        reader = csv.reader(f)
        next(reader)  # 欄位名稱
        next(reader)  # 量測方式
        next(reader)  # 工程單位
        for line in reader:
            if not line or not line[0]:
                continue
            ts = _parse_csv_timestamp(line[0], line[1])
            values = line[2:20]  # AI1..AI18（共 18 欄）
            rows.append((ts, values))
    return rows


def _build_lookup(
    datalog_root: Path, date_str: str
) -> dict[int, dict[datetime, Sample]]:
    """讀一個日期資料夾的全部 18 通道，回傳 channel → {timestamp: Sample}。"""
    day_dir = datalog_root / date_str
    lookup: dict[int, dict[datetime, Sample]] = {}
    for ch in range(18):
        samples = parse_day(day_dir, channel=ch)
        lookup[ch] = {s.timestamp: s for s in samples}
    return lookup


# ── 測試 ─────────────────────────────────────────────────────────────────────


def test_e2e_timestamps_and_values(
    sample_folder: Path, expected_pen_csv: Path
) -> None:
    """CSV 每一列都能在 parsers 的資料中找到對應 timestamp，且數值相符。"""
    expected = _read_expected_csv(expected_pen_csv)
    assert len(expected) == 709, f"預期 709 筆資料列，實際 {len(expected)}"

    datalog_root = sample_folder / "DataStore" / "BatchDataLog" / "DataLog"

    # 預先建立各日期的 lookup（僅讀取 CSV 內出現的日期）
    date_strs_needed = {ts.strftime("%Y%m%d") for ts, _ in expected}
    lookups: dict[str, dict[int, dict[datetime, Sample]]] = {
        d: _build_lookup(datalog_root, d) for d in date_strs_needed
    }

    for row_idx, (ts, csv_vals) in enumerate(expected):
        date_key = ts.strftime("%Y%m%d")
        ch_lookup = lookups[date_key]

        for ch, csv_val in enumerate(csv_vals):
            csv_val = csv_val.strip()
            sample = ch_lookup[ch].get(ts)
            assert sample is not None, (
                f"row {row_idx}: 找不到 ch{ch} 在 {ts} 的 sample"
            )

            if csv_val == "錯誤":
                assert sample.status == "斷線", (
                    f"row {row_idx} ch{ch}: 期望 status='斷線'，實際 '{sample.status}'"
                )
            else:
                assert sample.status == "ok", (
                    f"row {row_idx} ch{ch}: 期望 status='ok'，實際 '{sample.status}'"
                )
                assert sample.value == pytest.approx(float(csv_val), abs=0.05), (
                    f"row {row_idx} ch{ch} @ {ts}: "
                    f"期望 {csv_val}，實際 {sample.value:.1f}"
                )
