"""글로벌 단축키 등록 모듈."""

import logging
import threading
from typing import Callable, Optional

from pynput import keyboard

logger = logging.getLogger(__name__)

# 기본 단축키: Win+Shift+A
DEFAULT_HOTKEY = {keyboard.Key.cmd, keyboard.Key.shift, keyboard.KeyCode.from_char("a")}


class HotkeyManager:
    """글로벌 단축키를 등록하고 관리하는 클래스."""

    def __init__(
        self,
        callback: Callable[[], None],
        hotkey: Optional[set] = None,
    ) -> None:
        """HotkeyManager 초기화.

        Args:
            callback: 단축키가 눌렸을 때 실행할 콜백 함수.
            hotkey: 감지할 키 조합. None이면 기본값(Win+Shift+A) 사용.
        """
        self._callback = callback
        self._hotkey = hotkey or DEFAULT_HOTKEY
        self._current_keys: set = set()
        self._listener: Optional[keyboard.Listener] = None
        self._lock = threading.Lock()

    def _normalize_key(self, key: keyboard.Key | keyboard.KeyCode) -> keyboard.Key | keyboard.KeyCode:
        """키를 정규화하여 비교 가능하게 변환.

        Args:
            key: 입력된 키.

        Returns:
            정규화된 키.
        """
        if isinstance(key, keyboard.KeyCode) and key.char:
            return keyboard.KeyCode.from_char(key.char.lower())
        return key

    def _on_press(self, key: keyboard.Key | keyboard.KeyCode) -> None:
        """키 누름 이벤트 핸들러.

        Args:
            key: 눌린 키.
        """
        normalized = self._normalize_key(key)
        with self._lock:
            self._current_keys.add(normalized)
            if self._hotkey.issubset(self._current_keys):
                logger.info("단축키 감지!")
                self._current_keys.clear()
                try:
                    self._callback()
                except Exception as e:
                    logger.error("단축키 콜백 실행 실패: %s", e)

    def _on_release(self, key: keyboard.Key | keyboard.KeyCode) -> None:
        """키 놓음 이벤트 핸들러.

        Args:
            key: 놓은 키.
        """
        normalized = self._normalize_key(key)
        with self._lock:
            self._current_keys.discard(normalized)

    def start(self) -> None:
        """단축키 리스너 시작."""
        if self._listener is not None:
            logger.warning("리스너가 이미 실행 중입니다.")
            return

        self._listener = keyboard.Listener(
            on_press=self._on_press,
            on_release=self._on_release,
        )
        self._listener.daemon = True
        self._listener.start()
        logger.info("글로벌 단축키 리스너 시작")

    def stop(self) -> None:
        """단축키 리스너 중지."""
        if self._listener is not None:
            self._listener.stop()
            self._listener = None
            self._current_keys.clear()
            logger.info("글로벌 단축키 리스너 중지")

    @property
    def is_running(self) -> bool:
        """리스너 실행 중 여부."""
        return self._listener is not None and self._listener.is_alive()
