"""Downloads 새 파일 감지 시 오버레이 팝업."""

import logging
from pathlib import Path
from typing import Optional

from PyQt6.QtCore import Qt, QPropertyAnimation, QEasingCurve
from PyQt6.QtGui import QColor, QPainter, QFont
from PyQt6.QtWidgets import (
    QApplication,
    QComboBox,
    QDialog,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from src.project_manager import ProjectManager

logger = logging.getLogger(__name__)

# 파일 타입별 아이콘/라벨
FILE_TYPE_INFO = {
    ".pdf": ("PDF 문서", "#e74c3c"),
    ".doc": ("Word 문서", "#2b579a"),
    ".docx": ("Word 문서", "#2b579a"),
    ".xls": ("Excel 파일", "#217346"),
    ".xlsx": ("Excel 파일", "#217346"),
    ".ppt": ("PowerPoint", "#d24726"),
    ".pptx": ("PowerPoint", "#d24726"),
    ".png": ("이미지", "#9b59b6"),
    ".jpg": ("이미지", "#9b59b6"),
    ".jpeg": ("이미지", "#9b59b6"),
    ".gif": ("이미지", "#9b59b6"),
    ".txt": ("텍스트", "#3498db"),
    ".md": ("Markdown", "#3498db"),
    ".csv": ("CSV 데이터", "#27ae60"),
    ".json": ("JSON", "#f39c12"),
    ".mp4": ("동영상", "#8e44ad"),
    ".zip": ("압축 파일", "#95a5a6"),
    ".7z": ("압축 파일", "#95a5a6"),
}


class OverlayBackground(QWidget):
    """반투명 오버레이 배경."""

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        """OverlayBackground 초기화."""
        super().__init__(parent)
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

        # 전체 화면 크기로 설정
        screen = QApplication.primaryScreen()
        if screen:
            self.setGeometry(screen.geometry())

    def paintEvent(self, event) -> None:
        """반투명 배경 그리기."""
        painter = QPainter(self)
        painter.fillRect(self.rect(), QColor(0, 0, 0, 120))
        painter.end()


class DownloadPopup(QDialog):
    """새 다운로드 파일 감지 팝업."""

    def __init__(
        self,
        file_path: Path,
        project_manager: ProjectManager,
        parent: Optional[QWidget] = None,
    ) -> None:
        """DownloadPopup 초기화.

        Args:
            file_path: 감지된 파일 경로.
            project_manager: 프로젝트 매니저.
            parent: 부모 위젯.
        """
        super().__init__(parent)
        self._file_path = file_path
        self._pm = project_manager
        self._selected_project: Optional[str] = None
        self._new_project_name: Optional[str] = None
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
        self.setFixedWidth(420)

        # 메인 컨테이너
        container = QWidget(self)
        container.setObjectName("popupContainer")
        container.setStyleSheet("""
            #popupContainer {
                background: white;
                border-radius: 12px;
                border: 1px solid #ddd;
            }
        """)

        layout = QVBoxLayout(container)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(12)

        # 헤더
        header = QLabel("새 파일이 감지되었습니다")
        header.setFont(QFont("Segoe UI", 14, QFont.Weight.Bold))
        header.setStyleSheet("color: #333;")
        layout.addWidget(header)

        # 파일 정보
        suffix = self._file_path.suffix.lower()
        type_info = FILE_TYPE_INFO.get(suffix, ("파일", "#7f8c8d"))
        type_label, type_color = type_info

        file_info = QWidget()
        file_layout = QHBoxLayout(file_info)
        file_layout.setContentsMargins(12, 10, 12, 10)
        file_info.setStyleSheet(
            f"background: {type_color}15; border-radius: 8px; border: 1px solid {type_color}40;"
        )

        badge = QLabel(type_label)
        badge.setStyleSheet(
            f"background: {type_color}; color: white; padding: 2px 8px; "
            f"border-radius: 4px; font-size: 11px; font-weight: bold;"
        )
        badge.setFixedHeight(22)
        file_layout.addWidget(badge)

        fname = QLabel(self._file_path.name)
        fname.setStyleSheet("font-size: 13px; color: #333; font-weight: 500;")
        fname.setWordWrap(True)
        file_layout.addWidget(fname, 1)

        layout.addWidget(file_info)

        # 프로젝트 선택
        proj_label = QLabel("프로젝트에 추가:")
        proj_label.setStyleSheet("color: #666; font-size: 12px;")
        layout.addWidget(proj_label)

        self._project_combo = QComboBox()
        self._project_combo.setStyleSheet(
            "QComboBox { padding: 8px; border: 1px solid #ddd; border-radius: 6px; font-size: 13px; }"
        )
        self._refresh_projects()
        layout.addWidget(self._project_combo)

        # 새 프로젝트 생성 영역
        new_proj_widget = QWidget()
        new_proj_layout = QHBoxLayout(new_proj_widget)
        new_proj_layout.setContentsMargins(0, 0, 0, 0)

        self._new_proj_input = QLineEdit()
        self._new_proj_input.setPlaceholderText("새 프로젝트 이름 입력...")
        self._new_proj_input.setStyleSheet(
            "padding: 8px; border: 1px solid #ddd; border-radius: 6px; font-size: 13px;"
        )
        new_proj_layout.addWidget(self._new_proj_input, 1)

        self._create_btn = QPushButton("+ 생성")
        self._create_btn.setStyleSheet(
            "QPushButton { padding: 8px 12px; background: #27ae60; color: white; "
            "border: none; border-radius: 6px; font-size: 12px; font-weight: bold; }"
            "QPushButton:hover { background: #219a52; }"
        )
        self._create_btn.clicked.connect(self._on_create_project)
        new_proj_layout.addWidget(self._create_btn)

        layout.addWidget(new_proj_widget)

        # 버튼 영역
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(8)

        self._skip_btn = QPushButton("건너뛰기")
        self._skip_btn.setStyleSheet(
            "QPushButton { padding: 10px 20px; background: #f0f0f0; color: #666; "
            "border: none; border-radius: 6px; font-size: 13px; }"
            "QPushButton:hover { background: #e0e0e0; }"
        )
        self._skip_btn.clicked.connect(self.reject)
        btn_layout.addWidget(self._skip_btn)

        self._add_btn = QPushButton("추가하기")
        self._add_btn.setStyleSheet(
            "QPushButton { padding: 10px 20px; background: #3498db; color: white; "
            "border: none; border-radius: 6px; font-size: 13px; font-weight: bold; }"
            "QPushButton:hover { background: #2980b9; }"
        )
        self._add_btn.clicked.connect(self._on_add)
        btn_layout.addWidget(self._add_btn)

        layout.addLayout(btn_layout)

        # 다이얼로그 레이아웃
        dlg_layout = QVBoxLayout(self)
        dlg_layout.setContentsMargins(0, 0, 0, 0)
        dlg_layout.addWidget(container)
        self.adjustSize()

    def _refresh_projects(self) -> None:
        """프로젝트 목록 갱신."""
        self._project_combo.clear()
        projects = self._pm.list_projects()
        if projects:
            for proj in projects:
                self._project_combo.addItem(proj.name)
        else:
            self._project_combo.addItem("(프로젝트 없음 - 아래에서 생성)")
            self._add_btn.setEnabled(False)

    def _on_create_project(self) -> None:
        """새 프로젝트 생성."""
        name = self._new_proj_input.text().strip()
        if not name:
            return

        try:
            self._pm.create(name)
            self._new_proj_input.clear()
            self._refresh_projects()
            # 방금 만든 프로젝트 선택
            idx = self._project_combo.findText(name)
            if idx >= 0:
                self._project_combo.setCurrentIndex(idx)
            self._add_btn.setEnabled(True)
            logger.info("팝업에서 프로젝트 생성: %s", name)
        except ValueError as e:
            QMessageBox.warning(self, "생성 실패", str(e))

    def _on_add(self) -> None:
        """추가 버튼 클릭."""
        name = self._project_combo.currentText()
        if not name or name.startswith("("):
            return
        self._selected_project = name
        self.accept()

    def get_selected_project(self) -> Optional[str]:
        """선택된 프로젝트 이름 반환."""
        return self._selected_project

    def exec(self) -> int:
        """오버레이와 함께 다이얼로그 실행."""
        self._overlay.show()

        # 화면 중앙에 위치
        screen = QApplication.primaryScreen()
        if screen:
            geo = screen.geometry()
            x = geo.x() + (geo.width() - self.width()) // 2
            y = geo.y() + (geo.height() - self.height()) // 3
            self.move(x, y)

        result = super().exec()
        self._overlay.close()
        return result
