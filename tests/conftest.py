"""共用 pytest fixtures。"""
from pathlib import Path

import pytest


@pytest.fixture(scope="session")
def sample_folder() -> Path:
    """範例無紙紀錄器資料夾。"""
    return Path(__file__).resolve().parents[2] / "範例" / "無紙記錄器檔案"


@pytest.fixture(scope="session")
def expected_pen_csv() -> Path:
    """Windows 程式輸出的範例 Pen CSV（Big5）。"""
    return (
        Path(__file__).resolve().parents[2]
        / "範例"
        / "輸出檔案"
        / "042726141613_Pen.csv"
    )


@pytest.fixture(scope="session")
def expected_event_csv() -> Path:
    """Windows 程式輸出的範例 Event CSV（Big5）。"""
    return (
        Path(__file__).resolve().parents[2]
        / "範例"
        / "輸出檔案"
        / "042726141616_Event.csv"
    )
