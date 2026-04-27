"""Pn.dat + Pn.idx parser 測試。"""
from datetime import datetime, timedelta
from pathlib import Path

import pytest

from recorder2xlsx.format.data_log import Sample, parse_day


def test_first_sample_p0(sample_folder: Path) -> None:
    day_dir = sample_folder / "DataStore" / "BatchDataLog" / "DataLog" / "20260424"
    samples = parse_day(day_dir, channel=0)
    assert samples[0].timestamp == datetime(2026, 4, 24, 15, 47, 14, 183_000)
    assert samples[0].value == pytest.approx(22.8, abs=0.05)
    assert samples[0].status == "ok"


def test_second_sample_timestamp(sample_folder: Path) -> None:
    """第二筆時間 = 第一筆 + 1 秒，microsecond 部分不變。"""
    day_dir = sample_folder / "DataStore" / "BatchDataLog" / "DataLog" / "20260424"
    samples = parse_day(day_dir, channel=0)
    expected = datetime(2026, 4, 24, 15, 47, 15, 183_000)
    assert samples[1].timestamp == expected


def test_disconnect_status_p3(sample_folder: Path) -> None:
    """通道 3 = AI4，第一筆狀態 = 斷線。"""
    day_dir = sample_folder / "DataStore" / "BatchDataLog" / "DataLog" / "20260424"
    samples = parse_day(day_dir, channel=3)
    assert samples[0].status == "斷線"


def test_full_day_count(sample_folder: Path) -> None:
    """20260425 整天，1 秒 1 筆 → 55411 筆。"""
    day_dir = sample_folder / "DataStore" / "BatchDataLog" / "DataLog" / "20260425"
    samples = parse_day(day_dir, channel=0)
    assert len(samples) == 55411


def test_disconnect_day(sample_folder: Path) -> None:
    """20260427 只有 21 筆斷線 samples。"""
    day_dir = sample_folder / "DataStore" / "BatchDataLog" / "DataLog" / "20260427"
    samples = parse_day(day_dir, channel=0)
    assert len(samples) == 21
    assert all(s.status == "斷線" for s in samples)


def test_missing_files_raises(tmp_path: Path) -> None:
    from recorder2xlsx.format.errors import RecorderFormatError
    with pytest.raises(RecorderFormatError):
        parse_day(tmp_path, channel=0)
