"""프로젝트 목록/관리 윈도우."""

import logging
import os
import subprocess
import sys
from typing import Optional

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QHBoxLayout,
    QInputDialog,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from src.md_generator import generate_context_md
from src.project_manager import ProjectManager

logger = logging.getLogger(__name__)


class ProjectListWindow(QMainWindow):
    """프로젝트 목록 및 관리 메인 윈도우."""

    def __init__(
        self,
        project_manager: ProjectManager,
        parent: Optional[QWidget] = None,
    ) -> None:
        """ProjectListWindow 초기화.

        Args:
            project_manager: 프로젝트 매니저 인스턴스.
            parent: 부모 위젯.
        """
        super().__init__(parent)
        self._pm = project_manager
        self._setup_ui()
        self._refresh_list()

    def _setup_ui(self) -> None:
        """UI 구성."""
        self.setWindowTitle("Clickary - 프로젝트 관리")
        self.setMinimumSize(600, 400)

        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QHBoxLayout(central)

        # 왼쪽: 프로젝트 목록 + 버튼
        left_layout = QVBoxLayout()
        left_layout.addWidget(QLabel("프로젝트 목록"))

        self._list_widget = QListWidget()
        self._list_widget.currentItemChanged.connect(self._on_project_selected)
        left_layout.addWidget(self._list_widget)

        btn_layout = QHBoxLayout()
        self._new_btn = QPushButton("새 프로젝트")
        self._open_btn = QPushButton("폴더 열기")
        self._delete_btn = QPushButton("삭제")
        self._new_btn.clicked.connect(self._on_new_project)
        self._open_btn.clicked.connect(self._on_open_folder)
        self._delete_btn.clicked.connect(self._on_delete_project)
        btn_layout.addWidget(self._new_btn)
        btn_layout.addWidget(self._open_btn)
        btn_layout.addWidget(self._delete_btn)
        left_layout.addLayout(btn_layout)

        main_layout.addLayout(left_layout, 1)

        # 오른쪽: context.md 미리보기
        right_layout = QVBoxLayout()
        right_layout.addWidget(QLabel("context.md 미리보기"))
        self._preview = QTextEdit()
        self._preview.setReadOnly(True)
        right_layout.addWidget(self._preview)
        main_layout.addLayout(right_layout, 2)

    def _refresh_list(self) -> None:
        """프로젝트 목록 갱신."""
        self._list_widget.clear()
        for proj in self._pm.list_projects():
            item = QListWidgetItem(proj.name)
            item.setData(Qt.ItemDataRole.UserRole, proj.name)
            self._list_widget.addItem(item)

    def _on_project_selected(self, current: Optional[QListWidgetItem], _previous: Optional[QListWidgetItem]) -> None:
        """프로젝트 선택 시 context.md 미리보기 업데이트.

        Args:
            current: 현재 선택된 아이템.
            _previous: 이전 선택 아이템.
        """
        if current is None:
            self._preview.clear()
            return

        name = current.data(Qt.ItemDataRole.UserRole)
        try:
            project = self._pm.get(name)
            context_path = self._pm.data_dir / name / "context.md"

            # context.md가 없으면 생성
            if not context_path.exists():
                generate_context_md(
                    name,
                    self._pm.data_dir / name,
                    description=project.description,
                    created_at=project.created_at,
                )

            if context_path.exists():
                self._preview.setPlainText(
                    context_path.read_text(encoding="utf-8")
                )
            else:
                self._preview.setPlainText("(context.md 없음)")
        except KeyError:
            self._preview.setPlainText("(프로젝트를 찾을 수 없음)")

    def _on_new_project(self) -> None:
        """새 프로젝트 생성."""
        name, ok = QInputDialog.getText(self, "새 프로젝트", "프로젝트 이름:")
        if not ok or not name.strip():
            return

        desc, _ = QInputDialog.getText(self, "새 프로젝트", "설명 (선택):")

        try:
            self._pm.create(name.strip(), description=desc.strip())
            self._refresh_list()
            logger.info("프로젝트 생성: %s", name)
        except ValueError as e:
            QMessageBox.warning(self, "생성 실패", str(e))

    def _on_open_folder(self) -> None:
        """선택된 프로젝트 폴더를 파일 탐색기로 열기."""
        current = self._list_widget.currentItem()
        if current is None:
            return

        name = current.data(Qt.ItemDataRole.UserRole)
        folder = self._pm.data_dir / name
        if folder.exists():
            if sys.platform == "win32":
                os.startfile(str(folder))
            elif sys.platform == "darwin":
                subprocess.run(["open", str(folder)], check=False)
            else:
                subprocess.run(["xdg-open", str(folder)], check=False)

    def _on_delete_project(self) -> None:
        """선택된 프로젝트 삭제."""
        current = self._list_widget.currentItem()
        if current is None:
            return

        name = current.data(Qt.ItemDataRole.UserRole)
        reply = QMessageBox.question(
            self,
            "프로젝트 삭제",
            f"'{name}' 프로젝트와 모든 데이터를 삭제하시겠습니까?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes:
            try:
                self._pm.delete(name)
                self._refresh_list()
                self._preview.clear()
                logger.info("프로젝트 삭제: %s", name)
            except KeyError as e:
                QMessageBox.warning(self, "삭제 실패", str(e))
