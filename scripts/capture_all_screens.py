"""모든 UI 화면을 흰 배경 위에서 캡처 (개인정보 노출 방지)."""

import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import mss
from PIL import Image
from PyQt6.QtCore import Qt, QRect
from PyQt6.QtGui import QColor
from PyQt6.QtWidgets import QApplication, QWidget

DOCS_DIR = Path(__file__).parent.parent / "docs" / "screenshots"
DOCS_DIR.mkdir(parents=True, exist_ok=True)
DATA_DIR = Path(__file__).parent.parent / "data"


class WhiteBackground(QWidget):
    """전체 화면 흰색 배경."""

    def __init__(self):
        super().__init__()
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint)
        self.setStyleSheet("background: white;")
        screen = QApplication.primaryScreen()
        if screen:
            self.setGeometry(screen.geometry())
        self.showFullScreen()


def capture_widget(widget, filename, padding=4):
    """위젯 영역만 크롭 캡처."""
    screen_pos = widget.mapToGlobal(widget.rect().topLeft())
    w = widget.frameGeometry().width()
    h = widget.frameGeometry().height()
    with mss.mss() as sct:
        region = {
            "left": max(0, screen_pos.x() - padding),
            "top": max(0, screen_pos.y() - padding),
            "width": w + padding * 2,
            "height": h + padding * 2,
        }
        shot = sct.grab(region)
        img = Image.frombytes("RGB", shot.size, shot.bgra, "raw", "BGRX")
        path = DOCS_DIR / filename
        img.save(str(path))
        print(f"OK: {filename} ({img.size[0]}x{img.size[1]})")


def main():
    app = QApplication(sys.argv)

    # 흰 배경으로 화면 덮기
    bg = WhiteBackground()
    app.processEvents()
    time.sleep(0.3)

    from src.project_manager import ProjectManager
    pm = ProjectManager(data_dir=DATA_DIR)

    # 1. 프로젝트 관리 윈도우
    from src.ui.project_list import ProjectListWindow
    win = ProjectListWindow(pm)
    win.setWindowFlags(Qt.WindowType.WindowStaysOnTopHint)
    win.setGeometry(100, 100, 780, 520)
    win.show()
    win.raise_()
    for i in range(win._list_widget.count()):
        item = win._list_widget.item(i)
        if "Migration" in item.text():
            win._list_widget.setCurrentRow(i)
            break
    app.processEvents()
    time.sleep(0.5)
    app.processEvents()
    capture_widget(win, "01_project_window.png")
    print("1. Project window")
    win.close()

    # 2. 캡처 다이얼로그
    from src.ui.capture_dialog import CaptureDialog
    dlg = CaptureDialog(pm)
    dlg.setWindowFlags(Qt.WindowType.WindowStaysOnTopHint | Qt.WindowType.Dialog)
    dlg.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, False)
    dlg.setStyleSheet("background: white; border-radius: 12px;")
    dlg.show()
    dlg.raise_()
    # 화면 중앙
    screen = app.primaryScreen().geometry()
    dlg.move((screen.width() - dlg.width()) // 2, (screen.height() - dlg.height()) // 3)
    app.processEvents()
    time.sleep(0.3)
    app.processEvents()
    capture_widget(dlg, "02_capture_dialog.png")
    print("2. Capture dialog")

    # 3. 텍스트 입력 모드
    dlg._radio_text.setChecked(True)
    app.processEvents()
    time.sleep(0.2)
    dlg._text_input.setPlainText("Customer Meeting Notes\n- Migration timeline confirmed\n- SAP integration test completed\n- Next review: April 10")
    dlg._memo_edit.setText("Weekly sync notes")
    app.processEvents()
    time.sleep(0.1)
    capture_widget(dlg, "03_capture_text.png")
    print("3. Text input")
    dlg.close()
    if hasattr(dlg, '_overlay'):
        dlg._overlay.close()

    # 4. 다운로드 팝업
    from src.ui.download_popup import DownloadPopup
    fake_file = Path.home() / "Downloads" / "EDM_Collaboration_Overview.pdf"
    popup = DownloadPopup(fake_file, pm)
    popup.setWindowFlags(Qt.WindowType.WindowStaysOnTopHint | Qt.WindowType.Dialog)
    popup.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, False)
    popup.setStyleSheet("background: white; border-radius: 12px;")
    popup.show()
    popup.raise_()
    popup.move((screen.width() - popup.width()) // 2, (screen.height() - popup.height()) // 3)
    app.processEvents()
    time.sleep(0.3)
    app.processEvents()
    capture_widget(popup, "04_download_popup.png")
    print("4. Download popup")
    popup.close()
    if hasattr(popup, '_overlay'):
        popup._overlay.close()

    bg.close()
    print("\nDone! All widget-only on white background.")
    app.quit()


if __name__ == "__main__":
    main()
