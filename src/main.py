"""Clickary 앱 엔트리포인트 - 모든 모듈 통합."""

import logging
import sys
from pathlib import Path

from PyQt6.QtWidgets import QApplication, QMessageBox

from src.capture import capture_file, capture_pdf, capture_text
from src.file_watcher import FileWatcher
from src.hotkey import HotkeyManager
from src.md_generator import generate_context_md
from src.project_manager import ProjectManager
from src.sendto import install_sendto, is_installed
from src.tray import TrayApp
from src.ui.capture_dialog import CaptureDialog
from src.ui.project_list import ProjectListWindow

logger = logging.getLogger(__name__)

DATA_DIR = Path(__file__).parent.parent / "data"

PDF_EXTENSIONS = {".pdf"}
TEXT_EXTENSIONS = {".txt", ".md", ".csv", ".json"}


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

        # Downloads 폴더 감시
        self._file_watcher = FileWatcher(callback=self._on_new_download)

        # Windows Send To 설치
        self._ensure_sendto()

    def _ensure_sendto(self) -> None:
        """Send To 바로가기가 없으면 설치."""
        if sys.platform == "win32" and not is_installed():
            if install_sendto():
                logger.info("Send To 바로가기 설치 완료")

    def _on_new_download(self, file_path: Path) -> None:
        """Downloads 폴더에 새 파일 감지 시 처리.

        Args:
            file_path: 새로 다운로드된 파일 경로.
        """
        projects = self._pm.list_projects()
        if not projects:
            return

        from PyQt6.QtWidgets import QInputDialog
        project_names = [p.name for p in projects]
        name, ok = QInputDialog.getItem(
            None, "Clickary - 새 파일 감지",
            f"'{file_path.name}'을(를) 추가할 프로젝트:",
            project_names, 0, False,
        )
        if not ok:
            return

        captures_dir = self._pm.data_dir / name / "captures"
        notes_dir = self._pm.data_dir / name / "notes"
        suffix = file_path.suffix.lower()

        try:
            if suffix in PDF_EXTENSIONS:
                capture_pdf(captures_dir, notes_dir, file_path, description=file_path.stem)
            elif suffix in TEXT_EXTENSIONS:
                text = file_path.read_text(encoding="utf-8", errors="replace")
                capture_text(notes_dir, text, description=file_path.name)
            else:
                capture_file(captures_dir, file_path, description=file_path.stem)

            project = self._pm.get(name)
            generate_context_md(
                name, self._pm.data_dir / name,
                description=project.description,
                created_at=project.created_at,
            )
            logger.info("다운로드 파일 추가: %s → %s", file_path.name, name)

            # 프로젝트 윈도우 미리보기 갱신
            if self._project_window:
                self._project_window._refresh_preview()

        except Exception as e:
            logger.error("다운로드 파일 처리 실패: %s", e)

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
        self._file_watcher.start()
        self._show_project_window()

        try:
            return self._app.exec()
        finally:
            self._hotkey.stop()
            self._file_watcher.stop()
            logger.info("Clickary 종료")


def main() -> None:
    """메인 함수."""
    setup_logging()
    app = ClickaryApp()
    sys.exit(app.run())


if __name__ == "__main__":
    main()
