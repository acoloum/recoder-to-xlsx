"""PanelCfg.bin parser 測試。"""
from pathlib import Path

import pytest

from recorder2xlsx.format.panel_cfg import parse_panel_cfg


def test_pen_to_channel_mapping(sample_folder: Path) -> None:
    mapping = parse_panel_cfg(sample_folder / "PanelCfg.bin")
    assert len(mapping) == 18
    for pen, ch_idx in mapping.items():
        assert ch_idx == pen


def test_returns_dict(sample_folder: Path) -> None:
    mapping = parse_panel_cfg(sample_folder / "PanelCfg.bin")
    assert isinstance(mapping, dict)
    assert all(isinstance(k, int) and isinstance(v, int) for k, v in mapping.items())


def test_missing_file_raises(tmp_path: Path) -> None:
    with pytest.raises(Exception):
        parse_panel_cfg(tmp_path / "PanelCfg.bin")
