"""다운로드 감지 팝업 실제 동작 스크린샷 캡처."""

import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QApplication

DOCS_DIR = Path(__file__).parent.parent / "docs" / "screenshots"
DATA_DIR = Path(__file__).parent.parent / "data"


def save_widget(widget, filename):
    pixmap = widget.grab()
    path = DOCS_DIR / filename
    pixmap.save(str(path))
    print(f"  -> {filename} ({pixmap.width()}x{pixmap.height()})")


def main():
    app = QApplication(sys.argv)

    from src.project_manager import ProjectManager
    pm = ProjectManager(data_dir=DATA_DIR)

    # 다운로드 팝업 - 실제 파일명으로
    from src.ui.download_popup import DownloadPopup

    # 시나리오: 엑셀 파일 다운로드
    popup1 = DownloadPopup(
        Path.home() / "Downloads" / "부품특성추출결과_2602.xlsx", pm
    )
    popup1.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, False)
    popup1.setStyleSheet("background: white;")
    popup1.show()
    app.processEvents()
    time.sleep(0.3)
    app.processEvents()
    save_widget(popup1, "05_download_xlsx.png")
    popup1.close()
    if hasattr(popup1, '_overlay'):
        popup1._overlay.close()

    # 시나리오: PPT 파일 다운로드
    popup2 = DownloadPopup(
        Path.home() / "Downloads" / "CY26-03 EBS Korea Monthly Sync_20260320.pptx", pm
    )
    popup2.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, False)
    popup2.setStyleSheet("background: white;")
    popup2.show()
    app.processEvents()
    time.sleep(0.3)
    app.processEvents()
    save_widget(popup2, "06_download_pptx.png")
    popup2.close()
    if hasattr(popup2, '_overlay'):
        popup2._overlay.close()

    print("\nDone!")
    app.quit()


if __name__ == "__main__":
    main()
