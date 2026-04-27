"""TagCfg.bin parser 測試。"""
from pathlib import Path

import pytest

from recorder2xlsx.format.tag_cfg import Channel, parse_tag_cfg


def test_sample_18_channels(sample_folder: Path) -> None:
    channels = parse_tag_cfg(sample_folder / "TagCfg.bin")
    assert len(channels) == 18
    for i, ch in enumerate(channels, start=1):
        assert ch.name == f"AI{i}"
        assert ch.unit == "°C"
        assert ch.range_low == pytest.approx(-270.0)
        assert ch.range_high == pytest.approx(1370.0)


def test_last_channel_fields(sample_folder: Path) -> None:
    channels = parse_tag_cfg(sample_folder / "TagCfg.bin")
    ch = channels[17]
    assert ch.name == "AI18"
    assert ch.unit == "°C"
    assert ch.range_low == pytest.approx(-270.0, abs=0.01)
    assert ch.range_high == pytest.approx(1370.0, abs=0.01)


def test_channel_dataclass_immutable() -> None:
    import dataclasses
    ch = Channel(name="AI1", unit="°C", range_low=-270.0, range_high=1370.0)
    assert dataclasses.is_dataclass(ch)
    with pytest.raises(Exception):
        ch.name = "X"  # frozen dataclass 應無法修改


def test_missing_file_raises(tmp_path: Path) -> None:
    from recorder2xlsx.format.errors import RecorderFormatError
    with pytest.raises(RecorderFormatError):
        parse_tag_cfg(tmp_path / "TagCfg.bin")
