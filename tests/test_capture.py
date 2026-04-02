"""capture 모듈 테스트."""

import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from src.capture import (
    _save_metadata,
    _timestamp,
    capture_clipboard_text,
    capture_file,
    capture_screenshot,
    capture_text,
)


class TestHelpers:
    """헬퍼 함수 테스트."""

    def test_timestamp_format(self):
        """타임스탬프 형식 확인."""
        ts = _timestamp()
        assert len(ts) == 15  # YYYYMMDD_HHMMSS
        assert ts[8] == "_"

    def test_save_metadata_new(self, tmp_path):
        """새 메타데이터 파일 생성."""
        meta_path = tmp_path / "metadata.json"
        _save_metadata(meta_path, {"key": "value"})
        data = json.loads(meta_path.read_text(encoding="utf-8"))
        assert len(data) == 1
        assert data[0]["key"] == "value"

    def test_save_metadata_append(self, tmp_path):
        """기존 메타데이터에 추가."""
        meta_path = tmp_path / "metadata.json"
        _save_metadata(meta_path, {"first": True})
        _save_metadata(meta_path, {"second": True})
        data = json.loads(meta_path.read_text(encoding="utf-8"))
        assert len(data) == 2

    def test_save_metadata_corrupted(self, tmp_path):
        """손상된 메타데이터 파일 처리."""
        meta_path = tmp_path / "metadata.json"
        meta_path.write_text("bad json")
        _save_metadata(meta_path, {"recovered": True})
        data = json.loads(meta_path.read_text(encoding="utf-8"))
        assert len(data) == 1


class TestCaptureScreenshot:
    """스크린샷 캡처 테스트."""

    @patch("src.capture.mss")
    def test_capture_full_screen(self, mock_mss_module, tmp_path):
        """전체 화면 캡처."""
        captures_dir = tmp_path / "captures"

        # mss mock 설정
        mock_sct = MagicMock()
        mock_mss_module.mss.return_value.__enter__ = MagicMock(return_value=mock_sct)
        mock_mss_module.mss.return_value.__exit__ = MagicMock(return_value=False)
        mock_sct.monitors = [{"left": 0, "top": 0, "width": 100, "height": 100}]

        # 가짜 스크린샷 데이터 (4 bytes per pixel: BGRA)
        mock_grab = MagicMock()
        mock_grab.size = (100, 100)
        mock_grab.bgra = b"\x00\x00\xff\xff" * 10000  # 100x100 빨간 이미지
        mock_sct.grab.return_value = mock_grab

        filepath = capture_screenshot(captures_dir, description="테스트 캡처")

        assert filepath.exists()
        assert filepath.suffix == ".png"
        assert (captures_dir / "metadata.json").exists()

        meta = json.loads((captures_dir / "metadata.json").read_text(encoding="utf-8"))
        assert meta[0]["type"] == "screenshot"
        assert meta[0]["description"] == "테스트 캡처"

    @patch("src.capture.mss")
    def test_capture_region(self, mock_mss_module, tmp_path):
        """영역 캡처."""
        captures_dir = tmp_path / "captures"

        mock_sct = MagicMock()
        mock_mss_module.mss.return_value.__enter__ = MagicMock(return_value=mock_sct)
        mock_mss_module.mss.return_value.__exit__ = MagicMock(return_value=False)

        mock_grab = MagicMock()
        mock_grab.size = (50, 50)
        mock_grab.bgra = b"\x00\xff\x00\xff" * 2500
        mock_sct.grab.return_value = mock_grab

        region = {"left": 10, "top": 10, "width": 50, "height": 50}
        capture_screenshot(captures_dir, region=region)

        mock_sct.grab.assert_called_once_with(region)


class TestCaptureText:
    """텍스트 캡처 테스트."""

    def test_capture_text(self, tmp_path):
        """텍스트 직접 저장."""
        notes_dir = tmp_path / "notes"
        filepath = capture_text(notes_dir, "hello world", description="테스트 메모")

        assert filepath.exists()
        assert filepath.read_text(encoding="utf-8") == "hello world"
        meta = json.loads((notes_dir / "metadata.json").read_text(encoding="utf-8"))
        assert meta[0]["type"] == "text"
        assert meta[0]["description"] == "테스트 메모"

    def test_capture_empty_text_raises(self, tmp_path):
        """빈 텍스트 저장 시 ValueError."""
        with pytest.raises(ValueError, match="비어있습니다"):
            capture_text(tmp_path / "notes", "")
        with pytest.raises(ValueError, match="비어있습니다"):
            capture_text(tmp_path / "notes", "   ")

    @patch("src.capture.pyperclip")
    def test_capture_clipboard(self, mock_clip, tmp_path):
        """클립보드 텍스트 저장."""
        mock_clip.paste.return_value = "clipboard content"
        notes_dir = tmp_path / "notes"
        filepath = capture_clipboard_text(notes_dir, description="클립보드")

        assert filepath.exists()
        assert filepath.read_text(encoding="utf-8") == "clipboard content"

    @patch("src.capture.pyperclip")
    def test_capture_clipboard_empty_raises(self, mock_clip, tmp_path):
        """클립보드가 비어있을 때 ValueError."""
        mock_clip.paste.return_value = ""
        with pytest.raises(ValueError, match="텍스트가 없습니다"):
            capture_clipboard_text(tmp_path / "notes")


class TestCaptureFile:
    """파일 캡처 테스트."""

    def test_capture_file(self, tmp_path):
        """파일 복사."""
        source = tmp_path / "original.xlsx"
        source.write_text("data")
        captures_dir = tmp_path / "captures"

        filepath = capture_file(captures_dir, source, description="엑셀 파일")

        assert filepath.exists()
        assert filepath.read_text() == "data"
        assert "original" in filepath.name
        assert filepath.suffix == ".xlsx"

        meta = json.loads((captures_dir / "metadata.json").read_text(encoding="utf-8"))
        assert meta[0]["type"] == "file"
        assert meta[0]["original_name"] == "original.xlsx"

    def test_capture_file_not_found(self, tmp_path):
        """존재하지 않는 파일 복사 시 FileNotFoundError."""
        with pytest.raises(FileNotFoundError):
            capture_file(tmp_path / "captures", Path("/no/such/file.txt"))
