"""캡처 시 프로젝트 선택 다이얼로그."""

import logging
from pathlib import Path
from typing import Optional

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QComboBox,
    QDialog,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QRadioButton,
    QVBoxLayout,
)

from src.capture import capture_clipboard_text, capture_file, capture_screenshot, capture_text
from src.md_generator import generate_context_md
from src.project_manager import ProjectManager

logger = logging.getLogger(__name__)


class CaptureDialog(QDialog):
    """캡처 다이얼로그 - 프로젝트 선택 + 캡처 타입 선택 + 메모 입력."""

    def __init__(
        self,
        project_manager: ProjectManager,
        parent: Optional["QWidget"] = None,
    ) -> None:
        """CaptureDialog 초기화.

        Args:
            project_manager: 프로젝트 매니저 인스턴스.
            parent: 부모 위젯.
        """
        super().__init__(parent)
        self._pm = project_manager
        self._setup_ui()

    def _setup_ui(self) -> None:
        """UI 구성."""
        self.setWindowTitle("Clickary - 캡처")
        self.setFixedSize(360, 280)
        self.setWindowFlags(self.windowFlags() | Qt.WindowType.WindowStaysOnTopHint)

        layout = QVBoxLayout(self)

        # 프로젝트 선택
        layout.addWidget(QLabel("프로젝트:"))
        self._project_combo = QComboBox()
        self._refresh_projects()
        layout.addWidget(self._project_combo)

        # 캡처 타입 선택
        layout.addWidget(QLabel("캡처 타입:"))
        self._radio_screenshot = QRadioButton("스크린샷 (전체 화면)")
        self._radio_clipboard = QRadioButton("클립보드 텍스트")
        self._radio_text = QRadioButton("텍스트 직접 입력")
        self._radio_screenshot.setChecked(True)
        layout.addWidget(self._radio_screenshot)
        layout.addWidget(self._radio_clipboard)
        layout.addWidget(self._radio_text)

        # 메모 입력
        layout.addWidget(QLabel("메모 (선택):"))
        self._memo_edit = QLineEdit()
        self._memo_edit.setPlaceholderText("캡처에 대한 간단한 설명...")
        layout.addWidget(self._memo_edit)

        # 버튼
        btn_layout = QHBoxLayout()
        self._save_btn = QPushButton("저장")
        self._cancel_btn = QPushButton("취소")
        self._save_btn.clicked.connect(self._on_save)
        self._cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(self._save_btn)
        btn_layout.addWidget(self._cancel_btn)
        layout.addLayout(btn_layout)

    def _refresh_projects(self) -> None:
        """프로젝트 목록 갱신."""
        self._project_combo.clear()
        for proj in self._pm.list_projects():
            self._project_combo.addItem(proj.name)

    def _get_selected_project_name(self) -> Optional[str]:
        """선택된 프로젝트 이름 반환."""
        name = self._project_combo.currentText()
        return name if name else None

    def _get_capture_type(self) -> str:
        """선택된 캡처 타입 반환."""
        if self._radio_screenshot.isChecked():
            return "screenshot"
        if self._radio_clipboard.isChecked():
            return "clipboard"
        return "text"

    def _on_save(self) -> None:
        """저장 버튼 클릭 핸들러."""
        project_name = self._get_selected_project_name()
        if not project_name:
            QMessageBox.warning(self, "경고", "프로젝트를 선택하세요.")
            return

        try:
            project = self._pm.get(project_name)
        except KeyError:
            QMessageBox.warning(self, "경고", "프로젝트를 찾을 수 없습니다.")
            return

        capture_type = self._get_capture_type()
        memo = self._memo_edit.text().strip()
        captures_dir = self._pm.data_dir / project_name / "captures"
        notes_dir = self._pm.data_dir / project_name / "notes"

        try:
            if capture_type == "screenshot":
                capture_screenshot(captures_dir, description=memo)
            elif capture_type == "clipboard":
                capture_clipboard_text(notes_dir, description=memo)
            elif capture_type == "text":
                text = memo
                if not text:
                    QMessageBox.warning(self, "경고", "텍스트를 입력하세요.")
                    return
                capture_text(notes_dir, text, description=memo)

            # context.md 업데이트
            generate_context_md(
                project_name,
                self._pm.data_dir / project_name,
                description=project.description,
                created_at=project.created_at,
            )

            logger.info("캡처 완료: %s (%s)", project_name, capture_type)
            self.accept()

        except ValueError as e:
            QMessageBox.warning(self, "캡처 실패", str(e))
        except Exception as e:
            logger.error("캡처 실패: %s", e)
            QMessageBox.critical(self, "오류", f"캡처 중 오류 발생:\n{e}")
