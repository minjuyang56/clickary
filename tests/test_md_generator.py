"""md_generator 모듈 테스트."""

import json
from pathlib import Path

from src.md_generator import (
    _build_timeline,
    _format_timestamp,
    _load_metadata,
    _type_label,
    generate_context_md,
)


class TestHelpers:
    """헬퍼 함수 테스트."""

    def test_load_metadata(self, tmp_path):
        """메타데이터 로드."""
        meta_path = tmp_path / "metadata.json"
        meta_path.write_text(json.dumps([{"a": 1}]), encoding="utf-8")
        result = _load_metadata(meta_path)
        assert len(result) == 1
        assert result[0]["a"] == 1

    def test_load_metadata_missing(self, tmp_path):
        """존재하지 않는 파일."""
        assert _load_metadata(tmp_path / "nope.json") == []

    def test_load_metadata_corrupted(self, tmp_path):
        """손상된 파일."""
        meta_path = tmp_path / "metadata.json"
        meta_path.write_text("bad json")
        assert _load_metadata(meta_path) == []

    def test_format_timestamp(self):
        """타임스탬프 포맷."""
        assert _format_timestamp("2026-04-02T14:30:00") == "2026-04-02 14:30"

    def test_format_timestamp_invalid(self):
        """잘못된 타임스탬프."""
        assert _format_timestamp("not-a-date") == "not-a-date"

    def test_type_label(self):
        """타입 라벨 변환."""
        assert _type_label({"type": "screenshot"}) == "스크린샷"
        assert _type_label({"type": "file"}) == "파일"
        assert _type_label({"type": "text"}) == "텍스트"
        assert _type_label({"type": "clipboard_text"}) == "클립보드"
        assert _type_label({"type": "unknown"}) == "기타"
        assert _type_label({}) == "기타"

    def test_build_timeline_sorted(self):
        """타임라인 시간순 정렬."""
        captures = [{"timestamp": "2026-04-02T15:00:00", "type": "screenshot"}]
        notes = [{"timestamp": "2026-04-02T14:00:00", "type": "text"}]
        timeline = _build_timeline(captures, notes)
        assert len(timeline) == 2
        assert timeline[0]["type"] == "text"  # 14:00이 먼저
        assert timeline[1]["type"] == "screenshot"


class TestGenerateContextMd:
    """context.md 생성 테스트."""

    def _setup_project(self, tmp_path):
        """테스트용 프로젝트 디렉토리 세팅."""
        proj_dir = tmp_path / "test-project"
        captures_dir = proj_dir / "captures"
        notes_dir = proj_dir / "notes"
        captures_dir.mkdir(parents=True)
        notes_dir.mkdir(parents=True)
        return proj_dir, captures_dir, notes_dir

    def test_empty_project(self, tmp_path):
        """캡처 없는 빈 프로젝트."""
        proj_dir, _, _ = self._setup_project(tmp_path)
        result = generate_context_md("빈 프로젝트", proj_dir)
        assert result.exists()
        content = result.read_text(encoding="utf-8")
        assert "# 프로젝트: 빈 프로젝트" in content
        assert "캡처 수: 0건" in content

    def test_with_screenshot(self, tmp_path):
        """스크린샷이 있는 프로젝트."""
        proj_dir, captures_dir, _ = self._setup_project(tmp_path)

        meta = [{"type": "screenshot", "filename": "20260402_140000.png",
                 "timestamp": "2026-04-02T14:00:00", "description": "메인 화면"}]
        (captures_dir / "metadata.json").write_text(
            json.dumps(meta), encoding="utf-8"
        )

        result = generate_context_md("테스트", proj_dir, description="테스트 프로젝트")
        content = result.read_text(encoding="utf-8")
        assert "캡처 수: 1건" in content
        assert "스크린샷: 메인 화면" in content
        assert "captures/20260402_140000.png" in content

    def test_with_text_note(self, tmp_path):
        """텍스트 노트가 있는 프로젝트."""
        proj_dir, _, notes_dir = self._setup_project(tmp_path)

        # 노트 파일 생성
        (notes_dir / "20260402_150000.txt").write_text(
            "회의 내용 정리", encoding="utf-8"
        )
        meta = [{"type": "text", "filename": "20260402_150000.txt",
                 "timestamp": "2026-04-02T15:00:00", "description": "회의록"}]
        (notes_dir / "metadata.json").write_text(
            json.dumps(meta), encoding="utf-8"
        )

        result = generate_context_md("테스트", proj_dir)
        content = result.read_text(encoding="utf-8")
        assert "## 텍스트 노트" in content
        assert "회의록" in content
        assert "회의 내용 정리" in content

    def test_with_file_capture(self, tmp_path):
        """파일 캡처가 있는 프로젝트."""
        proj_dir, captures_dir, _ = self._setup_project(tmp_path)

        meta = [{"type": "file", "filename": "20260402_plan.xlsx",
                 "original_name": "plan.xlsx",
                 "timestamp": "2026-04-02T16:00:00", "description": "계획서"}]
        (captures_dir / "metadata.json").write_text(
            json.dumps(meta), encoding="utf-8"
        )

        result = generate_context_md("테스트", proj_dir)
        content = result.read_text(encoding="utf-8")
        assert "원본: plan.xlsx" in content

    def test_with_created_at(self, tmp_path):
        """생성일 포함."""
        proj_dir, _, _ = self._setup_project(tmp_path)
        result = generate_context_md(
            "테스트", proj_dir, created_at="2026-04-01T09:00:00"
        )
        content = result.read_text(encoding="utf-8")
        assert "생성일: 2026-04-01 09:00" in content

    def test_mixed_timeline(self, tmp_path):
        """여러 타입이 섞인 타임라인."""
        proj_dir, captures_dir, notes_dir = self._setup_project(tmp_path)

        captures_meta = [
            {"type": "screenshot", "filename": "ss.png",
             "timestamp": "2026-04-02T14:00:00", "description": "화면"},
        ]
        notes_meta = [
            {"type": "text", "filename": "note.txt",
             "timestamp": "2026-04-02T13:00:00", "description": "메모"},
        ]
        (notes_dir / "note.txt").write_text("메모 내용", encoding="utf-8")
        (captures_dir / "metadata.json").write_text(
            json.dumps(captures_meta), encoding="utf-8"
        )
        (notes_dir / "metadata.json").write_text(
            json.dumps(notes_meta), encoding="utf-8"
        )

        result = generate_context_md("혼합", proj_dir)
        content = result.read_text(encoding="utf-8")
        assert "캡처 수: 2건" in content
        # 타임라인에서 메모가 스크린샷보다 먼저 나와야 함
        memo_pos = content.index("메모")
        screen_pos = content.index("화면")
        assert memo_pos < screen_pos
