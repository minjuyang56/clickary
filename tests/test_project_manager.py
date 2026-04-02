"""project_manager 모듈 테스트."""

import json
import pytest
from pathlib import Path

from src.project_manager import Project, ProjectManager


@pytest.fixture
def tmp_data_dir(tmp_path):
    """임시 데이터 디렉토리를 사용하는 fixture."""
    return tmp_path / "data"


@pytest.fixture
def manager(tmp_data_dir):
    """ProjectManager 인스턴스 fixture."""
    return ProjectManager(data_dir=tmp_data_dir)


class TestProject:
    """Project 데이터클래스 테스트."""

    def test_project_creation(self):
        """프로젝트 생성 시 기본값 확인."""
        proj = Project(name="test-project")
        assert proj.name == "test-project"
        assert proj.description == ""
        assert proj.tags == []
        assert proj.created_at  # ISO 형식 문자열

    def test_project_paths(self):
        """프로젝트 경로 속성 확인."""
        proj = Project(name="my-proj")
        assert proj.captures_dir == proj.path / "captures"
        assert proj.notes_dir == proj.path / "notes"
        assert proj.context_md == proj.path / "context.md"


class TestProjectManager:
    """ProjectManager CRUD 테스트."""

    def test_create_project(self, manager, tmp_data_dir):
        """프로젝트 생성 및 디렉토리 확인."""
        proj = manager.create("my-project", description="테스트 프로젝트")
        assert proj.name == "my-project"
        assert proj.description == "테스트 프로젝트"
        assert (tmp_data_dir / "my-project" / "captures").is_dir()
        assert (tmp_data_dir / "my-project" / "notes").is_dir()

    def test_create_duplicate_raises(self, manager):
        """중복 이름 프로젝트 생성 시 ValueError."""
        manager.create("dup")
        with pytest.raises(ValueError, match="이미 존재"):
            manager.create("dup")

    def test_create_empty_name_raises(self, manager):
        """빈 이름으로 생성 시 ValueError."""
        with pytest.raises(ValueError, match="비어있을 수 없습니다"):
            manager.create("")
        with pytest.raises(ValueError, match="비어있을 수 없습니다"):
            manager.create("   ")

    def test_delete_project(self, manager, tmp_data_dir):
        """프로젝트 삭제 및 디렉토리 제거 확인."""
        manager.create("to-delete")
        assert (tmp_data_dir / "to-delete").is_dir()

        manager.delete("to-delete")
        assert not (tmp_data_dir / "to-delete").exists()
        assert not manager.exists("to-delete")

    def test_delete_nonexistent_raises(self, manager):
        """존재하지 않는 프로젝트 삭제 시 KeyError."""
        with pytest.raises(KeyError, match="찾을 수 없습니다"):
            manager.delete("ghost")

    def test_get_project(self, manager):
        """프로젝트 조회."""
        manager.create("proj-a", description="A 프로젝트")
        proj = manager.get("proj-a")
        assert proj.name == "proj-a"
        assert proj.description == "A 프로젝트"

    def test_get_nonexistent_raises(self, manager):
        """존재하지 않는 프로젝트 조회 시 KeyError."""
        with pytest.raises(KeyError):
            manager.get("nope")

    def test_list_projects(self, manager):
        """프로젝트 목록 조회 (생성 순)."""
        manager.create("z-last")
        manager.create("a-first")
        projects = manager.list_projects()
        assert len(projects) == 2
        # 생성 순서대로 (created_at 기준)
        assert projects[0].name == "z-last"
        assert projects[1].name == "a-first"

    def test_list_empty(self, manager):
        """빈 프로젝트 목록."""
        assert manager.list_projects() == []

    def test_exists(self, manager):
        """프로젝트 존재 여부 확인."""
        assert not manager.exists("nope")
        manager.create("yep")
        assert manager.exists("yep")

    def test_update_project(self, manager):
        """프로젝트 정보 업데이트."""
        manager.create("upd", description="old")
        proj = manager.update("upd", description="new", tags=["tag1"])
        assert proj.description == "new"
        assert proj.tags == ["tag1"]

    def test_update_partial(self, manager):
        """부분 업데이트 (description만)."""
        manager.create("partial", description="orig", tags=["a"])
        proj = manager.update("partial", description="changed")
        assert proj.description == "changed"
        assert proj.tags == ["a"]  # 변경 없음

    def test_update_nonexistent_raises(self, manager):
        """존재하지 않는 프로젝트 업데이트 시 KeyError."""
        with pytest.raises(KeyError):
            manager.update("ghost", description="x")

    def test_persistence(self, tmp_data_dir):
        """projects.json 저장/로드 확인."""
        mgr1 = ProjectManager(data_dir=tmp_data_dir)
        mgr1.create("persistent", description="saved")

        # 새 인스턴스로 로드
        mgr2 = ProjectManager(data_dir=tmp_data_dir)
        proj = mgr2.get("persistent")
        assert proj.name == "persistent"
        assert proj.description == "saved"

    def test_corrupted_json(self, tmp_data_dir):
        """손상된 projects.json 처리."""
        tmp_data_dir.mkdir(parents=True, exist_ok=True)
        (tmp_data_dir / "projects.json").write_text("not valid json")
        mgr = ProjectManager(data_dir=tmp_data_dir)
        assert mgr.list_projects() == []
