"""스크린샷/파일/텍스트 캡처 모듈."""

import json
import logging
import shutil
from datetime import datetime
from pathlib import Path
from typing import Optional

import mss
import pyperclip
from PIL import Image

logger = logging.getLogger(__name__)


def _timestamp() -> str:
    """현재 시간을 파일명용 문자열로 반환."""
    return datetime.now().strftime("%Y%m%d_%H%M%S")


def _save_metadata(meta_path: Path, metadata: dict) -> None:
    """메타데이터를 JSON 파일로 저장.

    Args:
        meta_path: 메타데이터 파일 경로.
        metadata: 저장할 메타데이터 딕셔너리.
    """
    existing: list[dict] = []
    if meta_path.exists():
        try:
            existing = json.loads(meta_path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, TypeError):
            existing = []
    existing.append(metadata)
    meta_path.write_text(
        json.dumps(existing, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def capture_screenshot(
    captures_dir: Path,
    description: str = "",
    region: Optional[dict] = None,
) -> Path:
    """전체 화면 또는 지정 영역 스크린샷을 캡처하여 저장.

    Args:
        captures_dir: 캡처 파일 저장 디렉토리.
        description: 스크린샷 설명.
        region: 캡처 영역 {"left", "top", "width", "height"}. None이면 전체 화면.

    Returns:
        저장된 스크린샷 파일 경로.
    """
    captures_dir.mkdir(parents=True, exist_ok=True)
    ts = _timestamp()
    filename = f"{ts}.png"
    filepath = captures_dir / filename

    with mss.mss() as sct:
        if region:
            monitor = {
                "left": region["left"],
                "top": region["top"],
                "width": region["width"],
                "height": region["height"],
            }
        else:
            monitor = sct.monitors[0]  # 전체 화면

        screenshot = sct.grab(monitor)
        img = Image.frombytes("RGB", screenshot.size, screenshot.bgra, "raw", "BGRX")
        img.save(str(filepath))

    logger.info("스크린샷 저장: %s", filepath)

    _save_metadata(
        captures_dir / "metadata.json",
        {
            "type": "screenshot",
            "filename": filename,
            "timestamp": datetime.now().isoformat(),
            "description": description,
            "region": region,
        },
    )
    return filepath


def capture_clipboard_text(
    notes_dir: Path,
    description: str = "",
) -> Path:
    """클립보드의 텍스트를 파일로 저장.

    Args:
        notes_dir: 노트 저장 디렉토리.
        description: 노트 설명.

    Returns:
        저장된 텍스트 파일 경로.

    Raises:
        ValueError: 클립보드에 텍스트가 없는 경우.
    """
    notes_dir.mkdir(parents=True, exist_ok=True)
    text = pyperclip.paste()
    if not text or not text.strip():
        raise ValueError("클립보드에 텍스트가 없습니다.")

    ts = _timestamp()
    filename = f"{ts}.txt"
    filepath = notes_dir / filename
    filepath.write_text(text, encoding="utf-8")
    logger.info("클립보드 텍스트 저장: %s", filepath)

    _save_metadata(
        notes_dir / "metadata.json",
        {
            "type": "clipboard_text",
            "filename": filename,
            "timestamp": datetime.now().isoformat(),
            "description": description,
        },
    )
    return filepath


def capture_text(
    notes_dir: Path,
    text: str,
    description: str = "",
) -> Path:
    """텍스트를 직접 받아서 파일로 저장.

    Args:
        notes_dir: 노트 저장 디렉토리.
        text: 저장할 텍스트.
        description: 노트 설명.

    Returns:
        저장된 텍스트 파일 경로.

    Raises:
        ValueError: 텍스트가 비어있는 경우.
    """
    if not text or not text.strip():
        raise ValueError("텍스트가 비어있습니다.")

    notes_dir.mkdir(parents=True, exist_ok=True)
    ts = _timestamp()
    filename = f"{ts}.txt"
    filepath = notes_dir / filename
    filepath.write_text(text, encoding="utf-8")
    logger.info("텍스트 저장: %s", filepath)

    _save_metadata(
        notes_dir / "metadata.json",
        {
            "type": "text",
            "filename": filename,
            "timestamp": datetime.now().isoformat(),
            "description": description,
        },
    )
    return filepath


def capture_file(
    captures_dir: Path,
    source_path: Path,
    description: str = "",
) -> Path:
    """파일을 프로젝트 captures 폴더로 복사.

    Args:
        captures_dir: 캡처 파일 저장 디렉토리.
        source_path: 원본 파일 경로.
        description: 파일 설명.

    Returns:
        복사된 파일 경로.

    Raises:
        FileNotFoundError: 원본 파일이 없는 경우.
    """
    if not source_path.exists():
        raise FileNotFoundError(f"파일을 찾을 수 없습니다: {source_path}")

    captures_dir.mkdir(parents=True, exist_ok=True)
    ts = _timestamp()
    suffix = source_path.suffix
    filename = f"{ts}_{source_path.stem}{suffix}"
    filepath = captures_dir / filename
    shutil.copy2(source_path, filepath)
    logger.info("파일 복사: %s → %s", source_path, filepath)

    _save_metadata(
        captures_dir / "metadata.json",
        {
            "type": "file",
            "filename": filename,
            "original_name": source_path.name,
            "timestamp": datetime.now().isoformat(),
            "description": description,
        },
    )
    return filepath
