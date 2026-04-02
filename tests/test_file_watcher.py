"""file_watcher 모듈 테스트."""

import time
from pathlib import Path
from unittest.mock import MagicMock

from src.file_watcher import DownloadHandler, FileWatcher, IGNORE_EXTENSIONS


class TestDownloadHandler:
    """DownloadHandler 테스트."""

    def test_should_handle_pdf(self, tmp_path):
        """PDF 파일 감지."""
        handler = DownloadHandler(MagicMock())
        pdf = tmp_path / "test.pdf"
        pdf.write_text("fake pdf")
        assert handler._should_handle(pdf)

    def test_should_handle_xlsx(self, tmp_path):
        """엑셀 파일 감지."""
        handler = DownloadHandler(MagicMock())
        xlsx = tmp_path / "data.xlsx"
        xlsx.write_text("fake xlsx")
        assert handler._should_handle(xlsx)

    def test_should_ignore_crdownload(self, tmp_path):
        """다운로드 중인 파일 무시."""
        handler = DownloadHandler(MagicMock())
        tmp_file = tmp_path / "file.crdownload"
        tmp_file.write_text("downloading")
        assert not handler._should_handle(tmp_file)

    def test_should_ignore_directory(self, tmp_path):
        """디렉토리 무시."""
        handler = DownloadHandler(MagicMock())
        subdir = tmp_path / "subdir"
        subdir.mkdir()
        assert not handler._should_handle(subdir)

    def test_should_handle_image(self, tmp_path):
        """이미지 파일 감지."""
        handler = DownloadHandler(MagicMock())
        img = tmp_path / "screenshot.png"
        img.write_text("fake png")
        assert handler._should_handle(img)


class TestFileWatcher:
    """FileWatcher 통합 테스트."""

    def test_start_stop(self, tmp_path):
        """감시 시작/중지."""
        callback = MagicMock()
        watcher = FileWatcher(callback, watch_dir=tmp_path)

        watcher.start()
        assert watcher.is_running

        watcher.stop()
        assert not watcher.is_running

    def test_detects_new_file(self, tmp_path):
        """새 파일 감지 확인."""
        callback = MagicMock()
        watcher = FileWatcher(callback, watch_dir=tmp_path, debounce_sec=0.5)
        watcher.start()

        try:
            # 새 파일 생성
            test_file = tmp_path / "report.pdf"
            test_file.write_text("pdf content")

            # 디바운스 대기
            time.sleep(1.5)

            callback.assert_called_once()
            called_path = callback.call_args[0][0]
            assert called_path.name == "report.pdf"
        finally:
            watcher.stop()

    def test_ignores_crdownload(self, tmp_path):
        """다운로드 중 파일 무시."""
        callback = MagicMock()
        watcher = FileWatcher(callback, watch_dir=tmp_path, debounce_sec=0.5)
        watcher.start()

        try:
            tmp_file = tmp_path / "file.crdownload"
            tmp_file.write_text("downloading")
            time.sleep(1.5)
            callback.assert_not_called()
        finally:
            watcher.stop()

    def test_nonexistent_dir(self, tmp_path):
        """존재하지 않는 디렉토리 감시 시도."""
        callback = MagicMock()
        watcher = FileWatcher(callback, watch_dir=tmp_path / "nope")
        watcher.start()
        assert not watcher.is_running

    def test_start_twice_no_duplicate(self, tmp_path):
        """중복 시작 방지."""
        callback = MagicMock()
        watcher = FileWatcher(callback, watch_dir=tmp_path)

        watcher.start()
        watcher.start()  # 두 번째는 무시
        assert watcher.is_running
        watcher.stop()
