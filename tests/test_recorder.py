"""recorder.py 聚合測試。"""
from pathlib import Path

from recorder2xlsx.core.recorder import load_recorder


def test_load_sample(sample_folder: Path) -> None:
    data = load_recorder(sample_folder)
    assert len(data.channels) == 18
    for ch_idx in range(18):
        assert len(data.samples[ch_idx]) > 100
    assert len(data.events) == 203


def test_channels_names(sample_folder: Path) -> None:
    data = load_recorder(sample_folder)
    names = [ch.name for ch in data.channels]
    assert names[0] == "AI1"
    assert names[17] == "AI18"
