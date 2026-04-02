"""모든 UI 화면을 순차적으로 띄우고 스크린샷 캡처."""

import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import mss
from PIL import Image
from PyQt6.QtCore import QTimer, Qt
from PyQt6.QtWidgets import QApplication

DOCS_DIR = Path(__file__).parent.parent / "docs" / "screenshots"
DATA_DIR = Path(__file__).parent.parent / "data"


def capture_screen(filename):
    """전체 화면 캡처."""
    with mss.mss() as sct:
        shot = sct.grab(sct.monitors[0])
        img = Image.frombytes("RGB", shot.size, shot.bgra, "raw", "BGRX")
        path = DOCS_DIR / filename
        img.save(str(path))
        print(f"OK: {filename} ({img.size[0]}x{img.size[1]})")


def capture_widget(widget, filename):
    """특정 위젯만 캡처."""
    geo = widget.frameGeometry()
    screen_pos = widget.mapToGlobal(widget.rect().topLeft())
    with mss.mss() as sct:
        region = {
            "left": screen_pos.x(),
            "top": screen_pos.y(),
            "width": geo.width(),
            "height": geo.height(),
        }
        shot = sct.grab(region)
        img = Image.frombytes("RGB", shot.size, shot.bgra, "raw", "BGRX")
        path = DOCS_DIR / filename
        img.save(str(path))
        print(f"OK: {filename} ({img.size[0]}x{img.size[1]})")


def main():
    app = QApplication(sys.argv)

    from src.project_manager import ProjectManager

    pm = ProjectManager(data_dir=DATA_DIR)

    # 1. 프로젝트 관리 윈도우
    from src.ui.project_list import ProjectListWindow
    win = ProjectListWindow(pm)
    win.show()
    win.raise_()
    # 첫 번째 프로젝트 선택
    if win._list_widget.count() > 0:
        win._list_widget.setCurrentRow(0)

    app.processEvents()
    time.sleep(0.5)
    app.processEvents()
    capture_widget(win, "01_project_list.png")
    print("1. Project list captured")

    # VBScript-Migration 선택 (context.md 보이게)
    for i in range(win._list_widget.count()):
        item = win._list_widget.item(i)
        if "Migration" in item.text():
            win._list_widget.setCurrentRow(i)
            break
    app.processEvents()
    time.sleep(0.3)
    app.processEvents()
    capture_widget(win, "02_project_preview.png")
    print("2. Project with preview captured")

    win.close()

    # 2. 캡처 다이얼로그
    from src.ui.capture_dialog import CaptureDialog
    dlg = CaptureDialog(pm)

    # overlay를 안 띄우고 다이얼로그만
    dlg.setWindowFlags(
        Qt.WindowType.WindowStaysOnTopHint | Qt.WindowType.Dialog
    )
    dlg.show()
    dlg.raise_()
    app.processEvents()
    time.sleep(0.3)
    app.processEvents()
    capture_widget(dlg, "03_capture_dialog.png")
    print("3. Capture dialog captured")

    # 텍스트 입력 모드
    dlg._radio_text.setChecked(True)
    app.processEvents()
    time.sleep(0.2)
    app.processEvents()
    dlg._text_input.setPlainText("회의 내용 정리:\n- Python 마이그레이션 일정 확정\n- SAP 연동 테스트 완료")
    dlg._memo_edit.setText("주간 미팅 노트")
    app.processEvents()
    capture_widget(dlg, "04_capture_text_input.png")
    print("4. Text input mode captured")

    dlg.close()
    if hasattr(dlg, '_overlay'):
        dlg._overlay.close()

    # 3. 다운로드 팝업
    from src.ui.download_popup import DownloadPopup
    fake_file = Path.home() / "Downloads" / "sample_report.pdf"
    popup = DownloadPopup(fake_file, pm)

    # overlay 없이 팝업만
    popup.setWindowFlags(
        Qt.WindowType.WindowStaysOnTopHint | Qt.WindowType.Dialog
    )
    popup.show()
    popup.raise_()
    app.processEvents()
    time.sleep(0.3)
    app.processEvents()
    capture_widget(popup, "05_download_popup.png")
    print("5. Download popup captured")

    popup.close()
    if hasattr(popup, '_overlay'):
        popup._overlay.close()

    # 4. 오버레이 + 다운로드 팝업 (전체 화면)
    popup2 = DownloadPopup(fake_file, pm)
    popup2._overlay.show()
    popup2.show()
    # 화면 중앙
    screen = app.primaryScreen()
    if screen:
        geo = screen.geometry()
        x = geo.x() + (geo.width() - popup2.width()) // 2
        y = geo.y() + (geo.height() - popup2.height()) // 3
        popup2.move(x, y)
    popup2.raise_()
    app.processEvents()
    time.sleep(0.5)
    app.processEvents()
    capture_screen("06_overlay_popup.png")
    print("6. Overlay + popup full screen captured")

    popup2.close()
    popup2._overlay.close()

    print("\nAll screenshots captured!")
    app.quit()


if __name__ == "__main__":
    main()
