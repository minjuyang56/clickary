"""캡처 시 프로젝트 선택 다이얼로그 (오버레이 스타일)."""

import logging
from pathlib import Path
from typing import Optional

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont
from PyQt6.QtWidgets import (
    QApplication,
    QComboBox,
    QDialog,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QRadioButton,
    QVBoxLayout,
    QWidget,
)

from src.capture import capture_clipboard_text, capture_file, capture_screenshot, capture_text
from src.md_generator import generate_context_md
from src.project_manager import ProjectManager
from src.ui.download_popup import OverlayBackground

logger = logging.getLogger(__name__)


class CaptureDialog(QDialog):
    """캡처 다이얼로그 - 오버레이 + 프로젝트 선택 + 캡처 타입."""

    def __init__(
        self,
        project_manager: ProjectManager,
        parent: Optional[QWidget] = None,
    ) -> None:
        """CaptureDialog 초기화."""
        super().__init__(parent)
        self._pm = project_manager
        self._overlay = OverlayBackground()
        self._setup_ui()

    def _setup_ui(self) -> None:
        """UI 구성."""
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.Dialog
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setFixedWidth(400)

        container = QWidget(self)
        container.setObjectName("captureContainer")
        container.setStyleSheet("""
            #captureContainer {
                background: white;
                border-radius: 12px;
                border: 1px solid #ddd;
            }
        """)

        layout = QVBoxLayout(container)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(12)

        # 헤더
        header = QLabel("캡처")
        header.setFont(QFont("Segoe UI", 14, QFont.Weight.Bold))
        header.setStyleSheet("color: #333;")
        layout.addWidget(header)

        # 프로젝트 선택
        proj_label = QLabel("프로젝트:")
        proj_label.setStyleSheet("color: #666; font-size: 12px;")
        layout.addWidget(proj_label)

        proj_row = QHBoxLayout()
        self._project_combo = QComboBox()
        self._project_combo.setStyleSheet(
            "QComboBox { padding: 8px; border: 1px solid #ddd; border-radius: 6px; font-size: 13px; }"
        )
        self._refresh_projects()
        proj_row.addWidget(self._project_combo, 1)

        self._new_proj_input = QLineEdit()
        self._new_proj_input.setPlaceholderText("새 프로젝트...")
        self._new_proj_input.setStyleSheet(
            "padding: 8px; border: 1px solid #ddd; border-radius: 6px; font-size: 12px;"
        )
        self._new_proj_input.setFixedWidth(120)
        proj_row.addWidget(self._new_proj_input)

        self._create_btn = QPushButton("+")
        self._create_btn.setFixedSize(34, 34)
        self._create_btn.setStyleSheet(
            "QPushButton { background: #27ae60; color: white; border: none; "
            "border-radius: 6px; font-size: 16px; font-weight: bold; }"
            "QPushButton:hover { background: #219a52; }"
        )
        self._create_btn.clicked.connect(self._on_create_project)
        proj_row.addWidget(self._create_btn)

        layout.addLayout(proj_row)

        # 캡처 타입
        type_label = QLabel("캡처 타입:")
        type_label.setStyleSheet("color: #666; font-size: 12px;")
        layout.addWidget(type_label)

        self._radio_screenshot = QRadioButton("스크린샷 (전체 화면)")
        self._radio_clipboard = QRadioButton("클립보드 텍스트")
        self._radio_text = QRadioButton("텍스트 직접 입력")
        self._radio_screenshot.setChecked(True)
        for r in [self._radio_screenshot, self._radio_clipboard, self._radio_text]:
            r.setStyleSheet("font-size: 13px; padding: 2px;")
            layout.addWidget(r)

        # 메모
        memo_label = QLabel("메모:")
        memo_label.setStyleSheet("color: #666; font-size: 12px;")
        layout.addWidget(memo_label)

        self._memo_edit = QLineEdit()
        self._memo_edit.setPlaceholderText("캡처에 대한 간단한 설명...")
        self._memo_edit.setStyleSheet(
            "padding: 8px; border: 1px solid #ddd; border-radius: 6px; font-size: 13px;"
        )
        layout.addWidget(self._memo_edit)

        # 버튼
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(8)

        self._cancel_btn = QPushButton("취소")
        self._cancel_btn.setStyleSheet(
            "QPushButton { padding: 10px 20px; background: #f0f0f0; color: #666; "
            "border: none; border-radius: 6px; font-size: 13px; }"
            "QPushButton:hover { background: #e0e0e0; }"
        )
        self._cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(self._cancel_btn)

        self._save_btn = QPushButton("저장")
        self._save_btn.setStyleSheet(
            "QPushButton { padding: 10px 20px; background: #3498db; color: white; "
            "border: none; border-radius: 6px; font-size: 13px; font-weight: bold; }"
            "QPushButton:hover { background: #2980b9; }"
        )
        self._save_btn.clicked.connect(self._on_save)
        btn_layout.addWidget(self._save_btn)

        layout.addLayout(btn_layout)

        dlg_layout = QVBoxLayout(self)
        dlg_layout.setContentsMargins(0, 0, 0, 0)
        dlg_layout.addWidget(container)
        self.adjustSize()

    def _refresh_projects(self) -> None:
        """프로젝트 목록 갱신."""
        self._project_combo.clear()
        for proj in self._pm.list_projects():
            self._project_combo.addItem(proj.name)

    def _on_create_project(self) -> None:
        """새 프로젝트 생성."""
        name = self._new_proj_input.text().strip()
        if not name:
            return
        try:
            self._pm.create(name)
            self._new_proj_input.clear()
            self._refresh_projects()
            idx = self._project_combo.findText(name)
            if idx >= 0:
                self._project_combo.setCurrentIndex(idx)
        except ValueError as e:
            QMessageBox.warning(self, "생성 실패", str(e))

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

    def exec(self) -> int:
        """오버레이와 함께 다이얼로그 실행."""
        self._overlay.show()

        screen = QApplication.primaryScreen()
        if screen:
            geo = screen.geometry()
            x = geo.x() + (geo.width() - self.width()) // 2
            y = geo.y() + (geo.height() - self.height()) // 3
            self.move(x, y)

        result = super().exec()
        self._overlay.close()
        return result
