"""Send To로 전달받은 파일을 Clickary 프로젝트에 추가하는 핸들러."""

import logging
import sys
from pathlib import Path

# 프로젝트 루트를 sys.path에 추가
PROJECT_ROOT = Path(__file__).parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from PyQt6.QtWidgets import QApplication, QInputDialog, QMessageBox

from src.capture import capture_file, capture_pdf, capture_text
from src.md_generator import generate_context_md
from src.project_manager import ProjectManager

logger = logging.getLogger(__name__)

DATA_DIR = PROJECT_ROOT / "data"
PDF_EXTENSIONS = {".pdf"}
TEXT_EXTENSIONS = {".txt", ".md", ".csv", ".json"}


def main() -> None:
    """Send To 핸들러 메인 함수."""
    logging.basicConfig(level=logging.INFO)

    files = [Path(f) for f in sys.argv[1:] if Path(f).exists()]
    if not files:
        return

    app = QApplication(sys.argv)
    pm = ProjectManager(data_dir=DATA_DIR)
    projects = pm.list_projects()

    if not projects:
        QMessageBox.warning(None, "Clickary", "프로젝트가 없습니다. 먼저 프로젝트를 생성하세요.")
        return

    project_names = [p.name for p in projects]
    name, ok = QInputDialog.getItem(
        None, "Clickary - 프로젝트 선택",
        f"{len(files)}개 파일을 추가할 프로젝트:",
        project_names, 0, False,
    )
    if not ok:
        return

    captures_dir = DATA_DIR / name / "captures"
    notes_dir = DATA_DIR / name / "notes"

    for file_path in files:
        suffix = file_path.suffix.lower()
        try:
            if suffix in PDF_EXTENSIONS:
                capture_pdf(captures_dir, notes_dir, file_path, description=file_path.stem)
            elif suffix in TEXT_EXTENSIONS:
                text = file_path.read_text(encoding="utf-8", errors="replace")
                capture_text(notes_dir, text, description=file_path.name)
            else:
                capture_file(captures_dir, file_path, description=file_path.stem)
            logger.info("파일 추가: %s → %s", file_path.name, name)
        except Exception as e:
            logger.error("파일 추가 실패 (%s): %s", file_path.name, e)

    project = pm.get(name)
    generate_context_md(name, DATA_DIR / name, description=project.description, created_at=project.created_at)

    QMessageBox.information(None, "Clickary", f"{len(files)}개 파일이 '{name}'에 추가되었습니다.")


if __name__ == "__main__":
    main()
