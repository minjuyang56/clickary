"""프로젝트 CRUD 및 데이터 관리 모듈."""

import json
import logging
import shutil
from dataclasses import asdict, dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

DATA_DIR = Path(__file__).parent.parent / "data"
PROJECTS_JSON = DATA_DIR / "projects.json"


@dataclass
class Project:
    """프로젝트 데이터 모델."""

    name: str
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    description: str = ""
    tags: list[str] = field(default_factory=list)

    @property
    def path(self) -> Path:
        """프로젝트 데이터 디렉토리 경로."""
        return DATA_DIR / self.name

    @property
    def captures_dir(self) -> Path:
        """캡처 파일 저장 디렉토리."""
        return self.path / "captures"

    @property
    def notes_dir(self) -> Path:
        """텍스트 노트 저장 디렉토리."""
        return self.path / "notes"

    @property
    def context_md(self) -> Path:
        """AI용 자동 생성 문서 경로."""
        return self.path / "context.md"


class ProjectManager:
    """프로젝트 생성/삭제/목록/선택을 관리하는 클래스."""

    def __init__(self, data_dir: Optional[Path] = None) -> None:
        """ProjectManager 초기화.

        Args:
            data_dir: 데이터 저장 루트 디렉토리. None이면 기본 경로 사용.
        """
        self.data_dir = data_dir or DATA_DIR
        self.projects_json = self.data_dir / "projects.json"
        self._ensure_data_dir()
        self._projects: dict[str, Project] = {}
        self._load_projects()

    def _ensure_data_dir(self) -> None:
        """데이터 디렉토리가 없으면 생성."""
        self.data_dir.mkdir(parents=True, exist_ok=True)

    def _load_projects(self) -> None:
        """projects.json에서 프로젝트 목록 로드."""
        if not self.projects_json.exists():
            self._projects = {}
            return
        try:
            data = json.loads(self.projects_json.read_text(encoding="utf-8"))
            self._projects = {
                name: Project(**info) for name, info in data.items()
            }
            logger.info("프로젝트 %d개 로드 완료", len(self._projects))
        except (json.JSONDecodeError, TypeError) as e:
            logger.error("projects.json 파싱 실패: %s", e)
            self._projects = {}

    def _save_projects(self) -> None:
        """프로젝트 목록을 projects.json에 저장."""
        data = {name: asdict(proj) for name, proj in self._projects.items()}
        self.projects_json.write_text(
            json.dumps(data, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        logger.info("projects.json 저장 완료")

    def _create_project_dirs(self, project: Project) -> None:
        """프로젝트용 하위 디렉토리(captures/, notes/) 생성."""
        proj_dir = self.data_dir / project.name
        (proj_dir / "captures").mkdir(parents=True, exist_ok=True)
        (proj_dir / "notes").mkdir(parents=True, exist_ok=True)
        logger.info("프로젝트 디렉토리 생성: %s", proj_dir)

    def create(self, name: str, description: str = "", tags: Optional[list[str]] = None) -> Project:
        """새 프로젝트 생성.

        Args:
            name: 프로젝트 이름 (디렉토리명으로도 사용).
            description: 프로젝트 설명.
            tags: 태그 목록.

        Returns:
            생성된 Project 객체.

        Raises:
            ValueError: 이름이 비어있거나 이미 존재하는 경우.
        """
        name = name.strip()
        if not name:
            raise ValueError("프로젝트 이름은 비어있을 수 없습니다.")
        if name in self._projects:
            raise ValueError(f"프로젝트 '{name}'이(가) 이미 존재합니다.")

        project = Project(
            name=name,
            description=description,
            tags=tags or [],
        )
        self._projects[name] = project
        self._create_project_dirs(project)
        self._save_projects()
        logger.info("프로젝트 생성: %s", name)
        return project

    def delete(self, name: str) -> None:
        """프로젝트 삭제 (데이터 디렉토리 포함).

        Args:
            name: 삭제할 프로젝트 이름.

        Raises:
            KeyError: 프로젝트가 존재하지 않는 경우.
        """
        if name not in self._projects:
            raise KeyError(f"프로젝트 '{name}'을(를) 찾을 수 없습니다.")

        proj_dir = self.data_dir / name
        if proj_dir.exists():
            shutil.rmtree(proj_dir)
            logger.info("프로젝트 디렉토리 삭제: %s", proj_dir)

        del self._projects[name]
        self._save_projects()
        logger.info("프로젝트 삭제: %s", name)

    def get(self, name: str) -> Project:
        """프로젝트 조회.

        Args:
            name: 프로젝트 이름.

        Returns:
            Project 객체.

        Raises:
            KeyError: 프로젝트가 존재하지 않는 경우.
        """
        if name not in self._projects:
            raise KeyError(f"프로젝트 '{name}'을(를) 찾을 수 없습니다.")
        return self._projects[name]

    def list_projects(self) -> list[Project]:
        """전체 프로젝트 목록 반환 (생성일 순).

        Returns:
            Project 객체 리스트.
        """
        return sorted(
            self._projects.values(),
            key=lambda p: p.created_at,
        )

    def exists(self, name: str) -> bool:
        """프로젝트 존재 여부 확인.

        Args:
            name: 프로젝트 이름.

        Returns:
            존재하면 True.
        """
        return name in self._projects

    def update(self, name: str, description: Optional[str] = None, tags: Optional[list[str]] = None) -> Project:
        """프로젝트 정보 업데이트.

        Args:
            name: 프로젝트 이름.
            description: 새 설명 (None이면 변경 없음).
            tags: 새 태그 목록 (None이면 변경 없음).

        Returns:
            업데이트된 Project 객체.

        Raises:
            KeyError: 프로젝트가 존재하지 않는 경우.
        """
        project = self.get(name)
        if description is not None:
            project.description = description
        if tags is not None:
            project.tags = tags
        self._save_projects()
        logger.info("프로젝트 업데이트: %s", name)
        return project
