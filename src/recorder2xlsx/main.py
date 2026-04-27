"""GUI 入口。"""
from __future__ import annotations

import sys

from PyQt5.QtWidgets import QApplication

from .gui.main_window import MainWindow


def main() -> None:
    app = QApplication(sys.argv)
    win = MainWindow()
    win.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
