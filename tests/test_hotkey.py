"""hotkey 모듈 테스트."""

from unittest.mock import MagicMock, patch

from pynput import keyboard

from src.hotkey import DEFAULT_HOTKEY, HotkeyManager


class TestHotkeyManager:
    """HotkeyManager 테스트."""

    def test_init_default_hotkey(self):
        """기본 단축키 설정 확인."""
        callback = MagicMock()
        mgr = HotkeyManager(callback)
        assert mgr._hotkey == DEFAULT_HOTKEY

    def test_init_custom_hotkey(self):
        """커스텀 단축키 설정."""
        callback = MagicMock()
        custom = {keyboard.Key.ctrl, keyboard.KeyCode.from_char("b")}
        mgr = HotkeyManager(callback, hotkey=custom)
        assert mgr._hotkey == custom

    def test_callback_triggered(self):
        """단축키 조합 시 콜백 호출 확인."""
        callback = MagicMock()
        mgr = HotkeyManager(callback)

        # Win+Shift+A 순서대로 누르기
        mgr._on_press(keyboard.Key.cmd)
        mgr._on_press(keyboard.Key.shift)
        mgr._on_press(keyboard.KeyCode.from_char("a"))

        callback.assert_called_once()

    def test_partial_keys_no_trigger(self):
        """부분 조합은 트리거되지 않음."""
        callback = MagicMock()
        mgr = HotkeyManager(callback)

        mgr._on_press(keyboard.Key.cmd)
        mgr._on_press(keyboard.Key.shift)
        # 'a' 없이 놓음

        callback.assert_not_called()

    def test_key_release(self):
        """키 릴리즈 시 current_keys에서 제거."""
        callback = MagicMock()
        mgr = HotkeyManager(callback)

        mgr._on_press(keyboard.Key.cmd)
        assert keyboard.Key.cmd in mgr._current_keys

        mgr._on_release(keyboard.Key.cmd)
        assert keyboard.Key.cmd not in mgr._current_keys

    def test_callback_error_handled(self):
        """콜백 에러가 전파되지 않음."""
        callback = MagicMock(side_effect=RuntimeError("test error"))
        mgr = HotkeyManager(callback)

        # 에러가 발생해도 예외가 전파되지 않아야 함
        mgr._on_press(keyboard.Key.cmd)
        mgr._on_press(keyboard.Key.shift)
        mgr._on_press(keyboard.KeyCode.from_char("a"))

        callback.assert_called_once()

    def test_normalize_key_uppercase(self):
        """대문자 키를 소문자로 정규화."""
        callback = MagicMock()
        mgr = HotkeyManager(callback)

        mgr._on_press(keyboard.Key.cmd)
        mgr._on_press(keyboard.Key.shift)
        mgr._on_press(keyboard.KeyCode.from_char("A"))  # 대문자

        callback.assert_called_once()

    @patch("src.hotkey.keyboard.Listener")
    def test_start_stop(self, mock_listener_cls):
        """리스너 시작/중지."""
        mock_listener = MagicMock()
        mock_listener.is_alive.return_value = True
        mock_listener_cls.return_value = mock_listener

        callback = MagicMock()
        mgr = HotkeyManager(callback)

        mgr.start()
        mock_listener.start.assert_called_once()
        assert mgr.is_running

        mgr.stop()
        mock_listener.stop.assert_called_once()

    @patch("src.hotkey.keyboard.Listener")
    def test_start_twice_no_duplicate(self, mock_listener_cls):
        """중복 시작 방지."""
        mock_listener = MagicMock()
        mock_listener.is_alive.return_value = True
        mock_listener_cls.return_value = mock_listener

        callback = MagicMock()
        mgr = HotkeyManager(callback)

        mgr.start()
        mgr.start()  # 두 번째 호출은 무시
        assert mock_listener_cls.call_count == 1
