"""Downloads 폴더 감시 모듈."""

import logging
import threading
import time
from pathlib import Path
from typing import Callable, Optional

from watchdog.events import FileSystemEvent, FileSystemEventHandler
from watchdog.observers import Observer

logger = logging.getLogger(__name__)

DOWNLOADS_DIR = Path.home() / "Downloads"

# 감시 대상 확장자
SUPPORTED_EXTENSIONS = {
    ".pdf", ".doc", ".docx", ".xls", ".xlsx", ".pptx", ".ppt",
    ".txt", ".md", ".csv", ".json",
    ".png", ".jpg", ".jpeg", ".gif", ".bmp",
    ".mp4", ".avi", ".mov",
    ".zip", ".7z", ".rar",
}

# 무시할 확장자 (다운로드 중인 파일 등)
IGNORE_EXTENSIONS = {".crdownload", ".tmp", ".part", ".download"}


class DownloadHandler(FileSystemEventHandler):
    """다운로드 폴더의 새 파일 감지 핸들러."""

    def __init__(self, callback: Callable[[Path], None], debounce_sec: float = 2.0) -> None:
        """DownloadHandler 초기화.

        Args:
            callback: 새 파일 감지 시 호출할 콜백. Path를 인자로 받음.
            debounce_sec: 디바운스 시간(초). 파일 쓰기 완료 대기.
        """
        super().__init__()
        self._callback = callback
        self._debounce_sec = debounce_sec
        self._pending: dict[str, threading.Timer] = {}
        self._lock = threading.Lock()

    def _should_handle(self, path: Path) -> bool:
        """처리 대상 파일인지 확인.

        Args:
            path: 파일 경로.

        Returns:
            처리해야 하면 True.
        """
        if not path.is_file():
            return False
        suffix = path.suffix.lower()
        if suffix in IGNORE_EXTENSIONS:
            return False
        if suffix in SUPPORTED_EXTENSIONS:
            return True
        return False

    def _fire_callback(self, filepath: str) -> None:
        """디바운스 후 콜백 실행.

        Args:
            filepath: 파일 경로 문자열.
        """
        path = Path(filepath)
        with self._lock:
            self._pending.pop(filepath, None)

        if path.exists() and self._should_handle(path):
            logger.info("새 파일 감지: %s", path.name)
            try:
                self._callback(path)
            except Exception as e:
                logger.error("파일 처리 콜백 실패: %s", e)

    def on_created(self, event: FileSystemEvent) -> None:
        """파일 생성 이벤트 핸들러.

        Args:
            event: 파일 시스템 이벤트.
        """
        if event.is_directory:
            return

        filepath = event.src_path
        with self._lock:
            # 기존 타이머 취소 후 새로 설정 (디바운스)
            old_timer = self._pending.pop(filepath, None)
            if old_timer:
                old_timer.cancel()
            timer = threading.Timer(self._debounce_sec, self._fire_callback, [filepath])
            timer.daemon = True
            self._pending[filepath] = timer
            timer.start()

    def on_modified(self, event: FileSystemEvent) -> None:
        """파일 수정 이벤트 핸들러 (다운로드 완료 감지용).

        Args:
            event: 파일 시스템 이벤트.
        """
        if event.is_directory:
            return
        # 수정 이벤트도 디바운스로 처리 (다운로드 중 여러 번 발생)
        self.on_created(event)


class FileWatcher:
    """Downloads 폴더를 감시하는 클래스."""

    def __init__(
        self,
        callback: Callable[[Path], None],
        watch_dir: Optional[Path] = None,
        debounce_sec: float = 2.0,
    ) -> None:
        """FileWatcher 초기화.

        Args:
            callback: 새 파일 감지 시 호출할 콜백.
            watch_dir: 감시할 디렉토리. None이면 ~/Downloads.
            debounce_sec: 디바운스 시간(초).
        """
        self._watch_dir = watch_dir or DOWNLOADS_DIR
        self._handler = DownloadHandler(callback, debounce_sec)
        self._observer: Optional[Observer] = None

    def start(self) -> None:
        """폴더 감시 시작."""
        if self._observer is not None:
            logger.warning("FileWatcher가 이미 실행 중입니다.")
            return

        if not self._watch_dir.exists():
            logger.error("감시 폴더가 존재하지 않습니다: %s", self._watch_dir)
            return

        self._observer = Observer()
        self._observer.schedule(self._handler, str(self._watch_dir), recursive=False)
        self._observer.daemon = True
        self._observer.start()
        logger.info("Downloads 폴더 감시 시작: %s", self._watch_dir)

    def stop(self) -> None:
        """폴더 감시 중지."""
        if self._observer is not None:
            self._observer.stop()
            self._observer.join(timeout=3)
            self._observer = None
            logger.info("Downloads 폴더 감시 중지")

    @property
    def is_running(self) -> bool:
        """감시 실행 중 여부."""
        return self._observer is not None and self._observer.is_alive()
