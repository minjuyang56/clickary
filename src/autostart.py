"""Windows 시작프로그램 자동 등록 모듈."""

import logging
import sys
from pathlib import Path

logger = logging.getLogger(__name__)

STARTUP_DIR = Path.home() / "AppData" / "Roaming" / "Microsoft" / "Windows" / "Start Menu" / "Programs" / "Startup"
BAT_NAME = "Clickary.bat"


def get_startup_path() -> Path:
    """시작프로그램 bat 파일 경로."""
    return STARTUP_DIR / BAT_NAME


def is_registered() -> bool:
    """시작프로그램에 등록되어 있는지 확인."""
    return get_startup_path().exists()


def register_autostart(python_exe: str | None = None) -> bool:
    """Windows 시작프로그램에 Clickary 등록.

    Args:
        python_exe: Python 실행 파일 경로. None이면 현재 인터프리터.

    Returns:
        등록 성공 여부.
    """
    if sys.platform != "win32":
        logger.warning("시작프로그램 등록은 Windows에서만 지원됩니다.")
        return False

    try:
        python_path = python_exe or sys.executable
        project_root = Path(__file__).parent.parent

        bat_content = (
            "@echo off\n"
            f'cd /d "{project_root}"\n'
            f'start /min "" "{python_path}" -m src.main\n'
        )
        get_startup_path().write_text(bat_content, encoding="utf-8")
        logger.info("시작프로그램 등록 완료: %s", get_startup_path())
        return True
    except Exception as e:
        logger.error("시작프로그램 등록 실패: %s", e)
        return False


def unregister_autostart() -> bool:
    """시작프로그램에서 Clickary 제거.

    Returns:
        제거 성공 여부.
    """
    try:
        path = get_startup_path()
        if path.exists():
            path.unlink()
            logger.info("시작프로그램 제거 완료")
            return True
        return False
    except Exception as e:
        logger.error("시작프로그램 제거 실패: %s", e)
        return False
