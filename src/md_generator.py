"""AI용 Markdown 인수인계 문서 자동 생성 모듈."""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)


def _load_metadata(meta_path: Path) -> list[dict]:
    """메타데이터 JSON 파일 로드.

    Args:
        meta_path: metadata.json 파일 경로.

    Returns:
        메타데이터 리스트. 파일이 없거나 파싱 실패 시 빈 리스트.
    """
    if not meta_path.exists():
        return []
    try:
        return json.loads(meta_path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, TypeError) as e:
        logger.warning("메타데이터 파싱 실패 (%s): %s", meta_path, e)
        return []


def _format_timestamp(iso_str: str) -> str:
    """ISO 타임스탬프를 읽기 좋은 형식으로 변환.

    Args:
        iso_str: ISO 8601 형식 문자열.

    Returns:
        'YYYY-MM-DD HH:MM' 형식 문자열.
    """
    try:
        dt = datetime.fromisoformat(iso_str)
        return dt.strftime("%Y-%m-%d %H:%M")
    except (ValueError, TypeError):
        return iso_str


def _build_timeline(captures_meta: list[dict], notes_meta: list[dict]) -> list[dict]:
    """캡처와 노트 메타데이터를 시간순으로 정렬.

    Args:
        captures_meta: captures 메타데이터 리스트.
        notes_meta: notes 메타데이터 리스트.

    Returns:
        시간순 정렬된 전체 항목 리스트.
    """
    all_items = []
    for item in captures_meta:
        item["_source"] = "captures"
        all_items.append(item)
    for item in notes_meta:
        item["_source"] = "notes"
        all_items.append(item)

    all_items.sort(key=lambda x: x.get("timestamp", ""))
    return all_items


def _type_label(item: dict) -> str:
    """캡처 타입에 대한 한글 라벨 반환.

    Args:
        item: 메타데이터 항목.

    Returns:
        한글 타입 라벨.
    """
    labels = {
        "screenshot": "스크린샷",
        "file": "파일",
        "pdf": "PDF 문서",
        "text": "텍스트",
        "clipboard_text": "클립보드",
        "pdf_extract": "PDF 추출",
    }
    return labels.get(item.get("type", ""), "기타")


def generate_context_md(
    project_name: str,
    project_dir: Path,
    description: str = "",
    created_at: Optional[str] = None,
) -> Path:
    """프로젝트의 context.md 파일을 생성/업데이트.

    Args:
        project_name: 프로젝트 이름.
        project_dir: 프로젝트 데이터 디렉토리.
        description: 프로젝트 설명.
        created_at: 프로젝트 생성일 (ISO 형식).

    Returns:
        생성된 context.md 파일 경로.
    """
    captures_dir = project_dir / "captures"
    notes_dir = project_dir / "notes"

    captures_meta = _load_metadata(captures_dir / "metadata.json")
    notes_meta = _load_metadata(notes_dir / "metadata.json")

    timeline = _build_timeline(captures_meta, notes_meta)
    total_count = len(timeline)
    now = datetime.now().strftime("%Y-%m-%d %H:%M")

    lines: list[str] = []

    # 헤더
    lines.append(f"# 프로젝트: {project_name}")
    lines.append("")

    # 개요
    lines.append("## 개요")
    if description:
        lines.append(f"- 설명: {description}")
    if created_at:
        lines.append(f"- 생성일: {_format_timestamp(created_at)}")
    lines.append(f"- 마지막 업데이트: {now}")
    lines.append(f"- 캡처 수: {total_count}건")
    lines.append("")

    # 타임라인
    if timeline:
        lines.append("## 타임라인")
        for item in timeline:
            ts = _format_timestamp(item.get("timestamp", ""))
            label = _type_label(item)
            desc = item.get("description", "")
            fname = item.get("filename", "")
            entry = f"- [{ts}] {label}: {desc}" if desc else f"- [{ts}] {label}: {fname}"
            lines.append(entry)
        lines.append("")

    # PDF 추출 문서 내용
    pdf_extracts = [
        i for i in timeline
        if i.get("type") == "pdf_extract"
    ]
    if pdf_extracts:
        lines.append("## 문서 내용 (PDF 추출)")
        for extract in pdf_extracts:
            ts = _format_timestamp(extract.get("timestamp", ""))
            original = extract.get("original_name", "")
            desc = extract.get("description", "") or original
            char_count = extract.get("char_count", 0)
            lines.append(f"### {desc} ({ts})")
            lines.append(f"*원본: {original} | {char_count}자 추출*")
            lines.append("")

            note_path = notes_dir / extract.get("filename", "")
            if note_path.exists():
                content = note_path.read_text(encoding="utf-8").strip()
                # 너무 길면 앞부분만 표시
                if len(content) > 3000:
                    content = content[:3000] + "\n\n... (이하 생략, 전문은 파일 참조)"
                lines.append(content)
            lines.append("")

    # 텍스트 노트 전문
    text_notes = [
        i for i in timeline
        if i.get("type") in ("text", "clipboard_text")
    ]
    if text_notes:
        lines.append("## 텍스트 노트")
        for note in text_notes:
            ts = _format_timestamp(note.get("timestamp", ""))
            desc = note.get("description", "") or note.get("filename", "")
            lines.append(f"### {desc} ({ts})")

            note_path = notes_dir / note.get("filename", "")
            if note_path.exists():
                content = note_path.read_text(encoding="utf-8").strip()
                lines.append(content)
            lines.append("")

    # 파일 목록
    capture_files = [
        i for i in timeline
        if i.get("type") in ("screenshot", "file", "pdf")
    ]
    if capture_files:
        lines.append("## 파일 목록")
        for item in capture_files:
            fname = item.get("filename", "")
            original = item.get("original_name", "")
            if original:
                lines.append(f"- captures/{fname} (원본: {original})")
            else:
                lines.append(f"- captures/{fname}")
        lines.append("")

    context_path = project_dir / "context.md"
    context_path.write_text("\n".join(lines), encoding="utf-8")
    logger.info("context.md 생성: %s", context_path)
    return context_path
