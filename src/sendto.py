"""Windows '보내기(Send To)' 메뉴 통합 모듈."""

import logging
import sys
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

SENDTO_DIR = Path.home() / "AppData" / "Roaming" / "Microsoft" / "Windows" / "SendTo"
SHORTCUT_NAME = "Clickary.lnk"


def get_sendto_path() -> Path:
    """Send To 디렉토리 내 Clickary 바로가기 경로.

    Returns:
        바로가기 파일 경로.
    """
    return SENDTO_DIR / SHORTCUT_NAME


def is_installed() -> bool:
    """Send To 메뉴에 Clickary가 설치되어 있는지 확인.

    Returns:
        설치되어 있으면 True.
    """
    # .lnk (winshell) 또는 .bat (fallback) 중 하나라도 있으면 설치된 것으로 판단
    return get_sendto_path().exists() or (SENDTO_DIR / "Clickary.bat").exists()


def install_sendto(python_exe: Optional[str] = None) -> bool:
    """Windows Send To 메뉴에 Clickary 바로가기 설치.

    Args:
        python_exe: Python 실행 파일 경로. None이면 현재 인터프리터 사용.

    Returns:
        설치 성공 여부.
    """
    if sys.platform != "win32":
        logger.warning("Send To 기능은 Windows에서만 지원됩니다.")
        return False

    try:
        import winshell
    except ImportError:
        # winshell 없으면 bat 파일로 대체
        return _install_bat_fallback(python_exe)

    try:
        python_path = python_exe or sys.executable
        script_path = str(Path(__file__).parent / "sendto_handler.py")
        shortcut_path = str(get_sendto_path())

        winshell.CreateShortcut(
            Path=shortcut_path,
            Target=python_path,
            Arguments=f'"{script_path}"',
            Description="Clickary로 파일 보내기",
        )
        logger.info("Send To 바로가기 설치 완료: %s", shortcut_path)
        return True
    except Exception as e:
        logger.error("Send To 설치 실패: %s", e)
        return False


def _install_bat_fallback(python_exe: Optional[str] = None) -> bool:
    """bat 파일로 Send To 바로가기 대체 설치.

    Args:
        python_exe: Python 실행 파일 경로.

    Returns:
        설치 성공 여부.
    """
    try:
        python_path = python_exe or sys.executable
        handler_path = Path(__file__).parent / "sendto_handler.py"
        bat_path = SENDTO_DIR / "Clickary.bat"

        bat_content = f'@echo off\n"{python_path}" "{handler_path}" %*\n'
        bat_path.write_text(bat_content, encoding="utf-8")
        logger.info("Send To bat 파일 설치 완료: %s", bat_path)
        return True
    except Exception as e:
        logger.error("Send To bat 설치 실패: %s", e)
        return False


def uninstall_sendto() -> bool:
    """Send To 메뉴에서 Clickary 제거.

    Returns:
        제거 성공 여부.
    """
    try:
        lnk_path = get_sendto_path()
        bat_path = SENDTO_DIR / "Clickary.bat"

        removed = False
        for path in [lnk_path, bat_path]:
            if path.exists():
                path.unlink()
                removed = True
                logger.info("Send To 제거: %s", path)

        return removed
    except Exception as e:
        logger.error("Send To 제거 실패: %s", e)
        return False
