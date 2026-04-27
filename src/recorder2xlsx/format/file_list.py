"""解析 FileList.ini，回傳基本識別資訊。"""
from __future__ import annotations

import configparser
from dataclasses import dataclass
from pathlib import Path

from .errors import RecorderFormatError


@dataclass(frozen=True)
class FileListInfo:
    instrument: str
    version: int


def parse_file_list(
    path: Path, *, expected_instrument: str = "PR"
) -> FileListInfo:
    """解析 FileList.ini，驗證儀器型號並回傳基本資訊。

    Parameters
    ----------
    path:
        FileList.ini 的路徑。
    expected_instrument:
        預期的 Instrument 值，預設為 "PR"。

    Returns
    -------
    FileListInfo
        包含 instrument 與 version 的資料物件。

    Raises
    ------
    RecorderFormatError
        找不到檔案、格式錯誤或 Instrument 不符時拋出。
    """
    if not path.is_file():
        raise RecorderFormatError(f"找不到 {path}")

    parser = configparser.ConfigParser()
    try:
        parser.read(path, encoding="utf-8")
    except configparser.Error as exc:
        raise RecorderFormatError(f"FileList.ini 格式錯誤：{exc}") from exc

    if "General" not in parser:
        raise RecorderFormatError("FileList.ini 缺少 [General] 區段")

    instrument = parser["General"].get("Instrument", "")
    version = parser["General"].getint("Ver", 0)

    if instrument != expected_instrument:
        raise RecorderFormatError(
            f"Instrument 預期為 {expected_instrument}，實際為 {instrument!r}"
        )

    return FileListInfo(instrument=instrument, version=version)
