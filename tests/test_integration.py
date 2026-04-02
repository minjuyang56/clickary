"""전체 워크플로우 통합 테스트.

프로젝트 생성 → 캡처 → MD 생성 확인.
"""

import json
from pathlib import Path

from src.capture import capture_file, capture_text
from src.md_generator import generate_context_md
from src.project_manager import ProjectManager


class TestIntegrationWorkflow:
    """프로젝트 생성 → 캡처 → MD 생성 전체 흐름 테스트."""

    def test_full_workflow(self, tmp_path):
        """전체 워크플로우: 프로젝트 생성 → 텍스트 캡처 → 파일 캡처 → context.md 생성."""
        # 1. 프로젝트 생성
        pm = ProjectManager(data_dir=tmp_path)
        project = pm.create("통합테스트", description="전체 흐름 테스트")
        assert pm.exists("통합테스트")
        assert (tmp_path / "통합테스트" / "captures").is_dir()
        assert (tmp_path / "통합테스트" / "notes").is_dir()

        # 2. 텍스트 캡처
        notes_dir = tmp_path / "통합테스트" / "notes"
        text_path = capture_text(
            notes_dir,
            "이것은 테스트 메모입니다.\n중요한 내용이 담겨있습니다.",
            description="테스트 메모",
        )
        assert text_path.exists()
        assert "테스트 메모" in text_path.read_text(encoding="utf-8")

        # 3. 파일 캡처
        captures_dir = tmp_path / "통합테스트" / "captures"
        source_file = tmp_path / "sample.xlsx"
        source_file.write_text("sample data")
        file_path = capture_file(
            captures_dir,
            source_file,
            description="샘플 파일",
        )
        assert file_path.exists()

        # 4. context.md 생성
        context_path = generate_context_md(
            "통합테스트",
            tmp_path / "통합테스트",
            description=project.description,
            created_at=project.created_at,
        )
        assert context_path.exists()

        content = context_path.read_text(encoding="utf-8")
        assert "# 프로젝트: 통합테스트" in content
        assert "전체 흐름 테스트" in content
        assert "캡처 수: 2건" in content
        assert "테스트 메모" in content
        assert "이것은 테스트 메모입니다." in content
        assert "sample.xlsx" in content

    def test_project_lifecycle(self, tmp_path):
        """프로젝트 생성 → 업데이트 → 삭제."""
        pm = ProjectManager(data_dir=tmp_path)

        # 생성
        pm.create("lifecycle", description="v1")
        assert pm.exists("lifecycle")

        # 업데이트
        proj = pm.update("lifecycle", description="v2", tags=["test"])
        assert proj.description == "v2"
        assert proj.tags == ["test"]

        # 영속성 확인
        pm2 = ProjectManager(data_dir=tmp_path)
        proj2 = pm2.get("lifecycle")
        assert proj2.description == "v2"

        # 삭제
        pm2.delete("lifecycle")
        assert not pm2.exists("lifecycle")
        assert not (tmp_path / "lifecycle").exists()

    def test_multiple_captures_timeline(self, tmp_path):
        """여러 캡처 후 타임라인 정렬 확인."""
        pm = ProjectManager(data_dir=tmp_path)
        pm.create("timeline-test")
        notes_dir = tmp_path / "timeline-test" / "notes"

        # 여러 텍스트 캡처
        capture_text(notes_dir, "첫 번째 메모", description="메모 1")
        capture_text(notes_dir, "두 번째 메모", description="메모 2")
        capture_text(notes_dir, "세 번째 메모", description="메모 3")

        # context.md 생성
        context_path = generate_context_md(
            "timeline-test",
            tmp_path / "timeline-test",
        )
        content = context_path.read_text(encoding="utf-8")
        assert "캡처 수: 3건" in content

        # 메타데이터 확인
        meta = json.loads(
            (notes_dir / "metadata.json").read_text(encoding="utf-8")
        )
        assert len(meta) == 3

    def test_empty_project_context_md(self, tmp_path):
        """캡처 없는 프로젝트도 context.md 생성 가능."""
        pm = ProjectManager(data_dir=tmp_path)
        pm.create("empty-project", description="비어있는 프로젝트")

        context_path = generate_context_md(
            "empty-project",
            tmp_path / "empty-project",
            description="비어있는 프로젝트",
        )
        content = context_path.read_text(encoding="utf-8")
        assert "캡처 수: 0건" in content
        assert "비어있는 프로젝트" in content
