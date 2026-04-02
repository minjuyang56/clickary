"""프로젝트 목록/관리 윈도우."""

import logging
import os
import subprocess
import sys
from pathlib import Path
from typing import Optional

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QDragEnterEvent, QDropEvent
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

from src.capture import capture_file, capture_pdf, capture_text
from src.md_generator import generate_context_md
from src.project_manager import ProjectManager

logger = logging.getLogger(__name__)

PDF_EXTENSIONS = {".pdf"}
IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".gif", ".bmp"}
TEXT_EXTENSIONS = {".txt", ".md", ".csv", ".json"}


class DropZoneLabel(QLabel):
    """드래그앤드롭 영역 라벨."""

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        """DropZoneLabel 초기화."""
        super().__init__(parent)
        self.setText("여기에 파일을 끌어다 놓으세요")
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setStyleSheet(
            "QLabel {"
            "  border: 2px dashed #aaa;"
            "  border-radius: 8px;"
            "  padding: 20px;"
            "  color: #888;"
            "  font-size: 13px;"
            "  background: #f9f9f9;"
            "}"
        )
        self.setMinimumHeight(60)


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
        self.setAcceptDrops(True)
        self._setup_ui()
        self._refresh_list()

    def _setup_ui(self) -> None:
        """UI 구성."""
        self.setWindowTitle("Clickary - 프로젝트 관리")
        self.setMinimumSize(650, 450)

        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QHBoxLayout(central)

        # 왼쪽: 프로젝트 목록 + 드롭존 + 버튼
        left_layout = QVBoxLayout()
        left_layout.addWidget(QLabel("프로젝트 목록"))

        self._list_widget = QListWidget()
        self._list_widget.currentItemChanged.connect(self._on_project_selected)
        left_layout.addWidget(self._list_widget)

        # 드래그앤드롭 영역
        self._drop_zone = DropZoneLabel()
        left_layout.addWidget(self._drop_zone)

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

    def _get_selected_project_name(self) -> Optional[str]:
        """현재 선택된 프로젝트 이름."""
        current = self._list_widget.currentItem()
        if current is None:
            return None
        return current.data(Qt.ItemDataRole.UserRole)

    # --- 드래그앤드롭 ---

    def dragEnterEvent(self, event: QDragEnterEvent) -> None:
        """드래그 진입 이벤트."""
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
            self._drop_zone.setStyleSheet(
                "QLabel {"
                "  border: 2px dashed #4a90d9;"
                "  border-radius: 8px;"
                "  padding: 20px;"
                "  color: #4a90d9;"
                "  font-size: 13px;"
                "  background: #e8f0fe;"
                "}"
            )
            self._drop_zone.setText("놓으면 선택된 프로젝트에 추가됩니다!")

    def dragLeaveEvent(self, event) -> None:
        """드래그 이탈 이벤트."""
        self._drop_zone.setStyleSheet(
            "QLabel {"
            "  border: 2px dashed #aaa;"
            "  border-radius: 8px;"
            "  padding: 20px;"
            "  color: #888;"
            "  font-size: 13px;"
            "  background: #f9f9f9;"
            "}"
        )
        self._drop_zone.setText("여기에 파일을 끌어다 놓으세요")

    def dropEvent(self, event: QDropEvent) -> None:
        """파일 드롭 이벤트."""
        self.dragLeaveEvent(event)  # 스타일 복원

        project_name = self._get_selected_project_name()
        if not project_name:
            QMessageBox.warning(self, "프로젝트 선택", "먼저 프로젝트를 선택하세요.")
            return

        urls = event.mimeData().urls()
        files = [Path(url.toLocalFile()) for url in urls if url.isLocalFile()]

        if not files:
            return

        added = 0
        for file_path in files:
            try:
                self._add_file_to_project(project_name, file_path)
                added += 1
            except Exception as e:
                logger.error("파일 추가 실패 (%s): %s", file_path.name, e)

        if added > 0:
            self._update_context_md(project_name)
            self._refresh_preview()
            QMessageBox.information(
                self, "완료", f"{added}개 파일이 '{project_name}'에 추가되었습니다."
            )

    def _add_file_to_project(self, project_name: str, file_path: Path) -> None:
        """파일을 프로젝트에 추가 (타입별 자동 처리).

        Args:
            project_name: 프로젝트 이름.
            file_path: 추가할 파일 경로.
        """
        captures_dir = self._pm.data_dir / project_name / "captures"
        notes_dir = self._pm.data_dir / project_name / "notes"
        suffix = file_path.suffix.lower()

        if suffix in PDF_EXTENSIONS:
            capture_pdf(captures_dir, notes_dir, file_path, description=file_path.stem)
            logger.info("PDF 추가: %s → %s", file_path.name, project_name)
        elif suffix in TEXT_EXTENSIONS:
            text = file_path.read_text(encoding="utf-8", errors="replace")
            capture_text(notes_dir, text, description=file_path.name)
            logger.info("텍스트 파일 추가: %s → %s", file_path.name, project_name)
        else:
            capture_file(captures_dir, file_path, description=file_path.stem)
            logger.info("파일 추가: %s → %s", file_path.name, project_name)

    def _update_context_md(self, project_name: str) -> None:
        """프로젝트의 context.md 업데이트."""
        try:
            project = self._pm.get(project_name)
            generate_context_md(
                project_name,
                self._pm.data_dir / project_name,
                description=project.description,
                created_at=project.created_at,
            )
        except KeyError:
            pass

    def _refresh_preview(self) -> None:
        """현재 선택된 프로젝트의 미리보기 갱신."""
        current = self._list_widget.currentItem()
        if current:
            self._on_project_selected(current, None)

    # --- 기존 이벤트 핸들러 ---

    def _on_project_selected(self, current: Optional[QListWidgetItem], _previous: Optional[QListWidgetItem]) -> None:
        """프로젝트 선택 시 context.md 미리보기 업데이트."""
        if current is None:
            self._preview.clear()
            return

        name = current.data(Qt.ItemDataRole.UserRole)
        try:
            project = self._pm.get(name)
            context_path = self._pm.data_dir / name / "context.md"

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
