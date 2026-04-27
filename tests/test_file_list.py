"""FileList.ini parser 測試。"""
from pathlib import Path

import pytest

from recorder2xlsx.format.errors import RecorderFormatError
from recorder2xlsx.format.file_list import FileListInfo, parse_file_list


def test_parse_sample(sample_folder: Path) -> None:
    info = parse_file_list(sample_folder / "FileList.ini")
    assert info.instrument == "PR"
    assert info.version == 242


def test_missing_file_raises(tmp_path: Path) -> None:
    with pytest.raises(RecorderFormatError):
        parse_file_list(tmp_path / "missing.ini")


def test_wrong_instrument_raises(tmp_path: Path) -> None:
    p = tmp_path / "FileList.ini"
    p.write_text("[General]\nInstrument=ABC\n", encoding="utf-8")
    with pytest.raises(RecorderFormatError):
        parse_file_list(p, expected_instrument="PR")
