"""시스템 트레이 아이콘 및 메뉴 모듈."""

import logging
from typing import Optional

from PyQt6.QtGui import QAction, QIcon
from PyQt6.QtWidgets import QApplication, QMenu, QSystemTrayIcon

logger = logging.getLogger(__name__)


class TrayApp(QSystemTrayIcon):
    """시스템 트레이 아이콘 앱."""

    def __init__(
        self,
        app: QApplication,
        on_capture: Optional[callable] = None,
        on_manage: Optional[callable] = None,
        icon_path: Optional[str] = None,
    ) -> None:
        """TrayApp 초기화.

        Args:
            app: QApplication 인스턴스.
            on_capture: 캡처 메뉴 클릭 콜백.
            on_manage: 프로젝트 관리 메뉴 클릭 콜백.
            icon_path: 트레이 아이콘 이미지 경로.
        """
        super().__init__()
        self._app = app
        self._on_capture = on_capture
        self._on_manage = on_manage

        if icon_path:
            self.setIcon(QIcon(icon_path))
        else:
            self.setIcon(self._app.style().standardIcon(
                self._app.style().StandardPixmap.SP_ComputerIcon
            ))

        self.setToolTip("Clickary - 프로젝트별 캡처 도구")
        self._setup_menu()
        self.activated.connect(self._on_activated)

    def _setup_menu(self) -> None:
        """트레이 우클릭 메뉴 구성."""
        menu = QMenu()

        capture_action = QAction("캡처", menu)
        capture_action.triggered.connect(self._handle_capture)
        menu.addAction(capture_action)

        manage_action = QAction("프로젝트 관리", menu)
        manage_action.triggered.connect(self._handle_manage)
        menu.addAction(manage_action)

        menu.addSeparator()

        quit_action = QAction("종료", menu)
        quit_action.triggered.connect(self._handle_quit)
        menu.addAction(quit_action)

        self.setContextMenu(menu)

    def _on_activated(self, reason: QSystemTrayIcon.ActivationReason) -> None:
        """트레이 아이콘 활성화 이벤트.

        Args:
            reason: 활성화 사유 (더블클릭 등).
        """
        if reason == QSystemTrayIcon.ActivationReason.DoubleClick:
            self._handle_manage()

    def _handle_capture(self) -> None:
        """캡처 메뉴 핸들러."""
        if self._on_capture:
            try:
                self._on_capture()
            except Exception as e:
                logger.error("캡처 핸들러 실행 실패: %s", e)

    def _handle_manage(self) -> None:
        """프로젝트 관리 메뉴 핸들러."""
        if self._on_manage:
            try:
                self._on_manage()
            except Exception as e:
                logger.error("관리 핸들러 실행 실패: %s", e)

    def _handle_quit(self) -> None:
        """앱 종료."""
        logger.info("Clickary 종료")
        self._app.quit()
