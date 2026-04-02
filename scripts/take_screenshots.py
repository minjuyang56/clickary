"""각 UI 화면 스크린샷 캡처 스크립트."""

import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import mss
from PIL import Image

DOCS_DIR = Path(__file__).parent.parent / "docs" / "screenshots"


def capture_screen(filename: str, region=None):
    """화면 캡처."""
    with mss.mss() as sct:
        monitor = region or sct.monitors[0]
        shot = sct.grab(monitor)
        img = Image.frombytes("RGB", shot.size, shot.bgra, "raw", "BGRX")
        path = DOCS_DIR / filename
        img.save(str(path))
        print(f"Captured: {path} ({img.size[0]}x{img.size[1]})")
        return path


if __name__ == "__main__":
    # 1. 현재 화면 전체 캡처 (트레이 아이콘 포함)
    capture_screen("01_tray_background.png")
    print("Done. Now trigger each UI manually and run this script with an argument.")
