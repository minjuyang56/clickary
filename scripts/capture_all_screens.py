"""Qt widget.grab()으로 정확한 위젯 캡처."""

import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QApplication

DOCS_DIR = Path(__file__).parent.parent / "docs" / "screenshots"
DOCS_DIR.mkdir(parents=True, exist_ok=True)
DATA_DIR = Path(__file__).parent.parent / "data"


def save_widget(widget, filename):
    """widget.grab()으로 정확히 캡처."""
    pixmap = widget.grab()
    path = DOCS_DIR / filename
    pixmap.save(str(path))
    print(f"  -> {filename} ({pixmap.width()}x{pixmap.height()})")


def main():
    app = QApplication(sys.argv)

    from src.project_manager import ProjectManager
    pm = ProjectManager(data_dir=DATA_DIR)

    # 1. 프로젝트 관리 윈도우
    from src.ui.project_list import ProjectListWindow
    win = ProjectListWindow(pm)
    win.resize(820, 560)
    win.show()
    for i in range(win._list_widget.count()):
        if "Migration" in win._list_widget.item(i).text():
            win._list_widget.setCurrentRow(i)
            break
    app.processEvents()
    time.sleep(0.5)
    app.processEvents()
    save_widget(win, "01_project_window.png")
    win.close()

    # 2. 캡처 다이얼로그 (기본)
    from src.ui.capture_dialog import CaptureDialog
    dlg1 = CaptureDialog(pm)
    dlg1.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, False)
    dlg1.setStyleSheet("background: white;")
    dlg1.show()
    app.processEvents()
    time.sleep(0.3)
    app.processEvents()
    save_widget(dlg1, "02_capture_dialog.png")
    dlg1.close()
    if hasattr(dlg1, '_overlay'):
        dlg1._overlay.close()

    # 3. 텍스트 입력 모드
    dlg2 = CaptureDialog(pm)
    dlg2.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, False)
    dlg2.setStyleSheet("background: white;")
    dlg2._radio_text.setChecked(True)
    app.processEvents()
    dlg2._text_input.setPlainText(
        "Customer Meeting Notes\n"
        "- Migration timeline confirmed\n"
        "- SAP integration test completed\n"
        "- Next review: April 10"
    )
    dlg2._memo_edit.setText("Weekly sync notes")
    dlg2.show()
    app.processEvents()
    time.sleep(0.3)
    app.processEvents()
    save_widget(dlg2, "03_capture_text.png")
    dlg2.close()
    if hasattr(dlg2, '_overlay'):
        dlg2._overlay.close()

    # 4. 다운로드 팝업
    from src.ui.download_popup import DownloadPopup
    fake_file = Path.home() / "Downloads" / "EDM_Collaboration_Overview.pdf"
    popup = DownloadPopup(fake_file, pm)
    popup.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, False)
    popup.setStyleSheet("background: white;")
    popup.show()
    app.processEvents()
    time.sleep(0.3)
    app.processEvents()
    save_widget(popup, "04_download_popup.png")
    popup.close()
    if hasattr(popup, '_overlay'):
        popup._overlay.close()

    print("\nDone!")
    app.quit()


if __name__ == "__main__":
    main()
