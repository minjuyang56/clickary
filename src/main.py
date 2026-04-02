"""Clickary 앱 엔트리포인트 - 모든 모듈 통합."""

import logging
import sys
from pathlib import Path

from PyQt6.QtWidgets import QApplication

from src.hotkey import HotkeyManager
from src.project_manager import ProjectManager
from src.tray import TrayApp
from src.ui.capture_dialog import CaptureDialog
from src.ui.project_list import ProjectListWindow

logger = logging.getLogger(__name__)

DATA_DIR = Path(__file__).parent.parent / "data"


def setup_logging() -> None:
    """로깅 설정."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )


class ClickaryApp:
    """Clickary 메인 애플리케이션."""

    def __init__(self) -> None:
        """ClickaryApp 초기화."""
        self._app = QApplication(sys.argv)
        self._app.setApplicationName("Clickary")
        self._app.setQuitOnLastWindowClosed(False)

        self._pm = ProjectManager(data_dir=DATA_DIR)
        self._project_window: ProjectListWindow | None = None

        # 시스템 트레이
        self._tray = TrayApp(
            self._app,
            on_capture=self._show_capture_dialog,
            on_manage=self._show_project_window,
        )

        # 글로벌 단축키
        self._hotkey = HotkeyManager(callback=self._show_capture_dialog)

    def _show_capture_dialog(self) -> None:
        """캡처 다이얼로그 표시."""
        dialog = CaptureDialog(self._pm)
        dialog.exec()

    def _show_project_window(self) -> None:
        """프로젝트 관리 윈도우 표시."""
        if self._project_window is None:
            self._project_window = ProjectListWindow(self._pm)
        self._project_window.show()
        self._project_window.raise_()
        self._project_window.activateWindow()

    def run(self) -> int:
        """앱 실행.

        Returns:
            종료 코드.
        """
        logger.info("Clickary 시작")
        self._tray.show()
        self._hotkey.start()

        try:
            return self._app.exec()
        finally:
            self._hotkey.stop()
            logger.info("Clickary 종료")


def main() -> None:
    """메인 함수."""
    setup_logging()
    app = ClickaryApp()
    sys.exit(app.run())


if __name__ == "__main__":
    main()
