"""Alarm.lst parser 測試。"""
from datetime import datetime
from pathlib import Path

import pytest

from recorder2xlsx.format.alarm_log import Event, parse_alarm_log


def test_total_count(sample_folder: Path) -> None:
    events = parse_alarm_log(
        sample_folder / "DataStore" / "BatchAlarm" / "Alarm" / "Alarm.lst"
    )
    assert len(events) == 203


def test_last_three_events(sample_folder: Path) -> None:
    events = parse_alarm_log(
        sample_folder / "DataStore" / "BatchAlarm" / "Alarm" / "Alarm.lst"
    )
    e1, e2, e3 = events[-3], events[-2], events[-1]
    assert e1.action == "卸載"
    assert e1.occurred_at == datetime(2026, 4, 25, 15, 23, 12)
    assert e2.action == "更新"
    assert e2.occurred_at == datetime(2026, 4, 25, 15, 23, 30)
    assert e3.action == "開機"
    assert e3.occurred_at == datetime(2026, 4, 27, 14, 1, 14)


def test_event_fields(sample_folder: Path) -> None:
    events = parse_alarm_log(
        sample_folder / "DataStore" / "BatchAlarm" / "Alarm" / "Alarm.lst"
    )
    for e in events:
        assert e.source == ""
        assert e.cleared_at is None
        assert e.value == ""
        assert e.acknowledged is False


def test_empty_file(tmp_path: Path) -> None:
    f = tmp_path / "Alarm.lst"
    import struct
    header = struct.pack('<IHHH', 0, 1000, 304, 0) + b'\x00' * 10
    f.write_bytes(header)
    assert parse_alarm_log(f) == []


def test_missing_file_raises(tmp_path: Path) -> None:
    from recorder2xlsx.format.errors import RecorderFormatError
    with pytest.raises(RecorderFormatError):
        parse_alarm_log(tmp_path / "nonexistent.lst")
