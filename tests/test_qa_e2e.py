"""End-to-end QA tests for Clickary desktop app.

Tests simulate real user actions programmatically and verify each feature works.
"""

import json
import shutil
import tempfile
import threading
import time
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

# Ensure src is importable
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.project_manager import ProjectManager, Project
from src.capture import capture_text, capture_file, capture_pdf, capture_screenshot, _save_metadata
from src.md_generator import generate_context_md
from src.file_watcher import FileWatcher, DownloadHandler, SUPPORTED_EXTENSIONS
from src.autostart import register_autostart, get_startup_path, is_registered, unregister_autostart
from src.sendto import install_sendto, get_sendto_path, uninstall_sendto, SENDTO_DIR


@pytest.fixture
def tmp_data_dir(tmp_path):
    """Provide a temporary data directory for tests."""
    return tmp_path / "data"


@pytest.fixture
def pm(tmp_data_dir):
    """Provide a ProjectManager with temp data dir."""
    return ProjectManager(data_dir=tmp_data_dir)


@pytest.fixture
def project(pm):
    """Create and return a test project."""
    return pm.create("QA-Test-Project", description="E2E QA test project", tags=["qa", "test"])


class TestProjectCreation:
    """Test 1: Project creation via ProjectManager API."""

    def test_create_project_directories(self, pm, tmp_data_dir):
        proj = pm.create("QA-Test-Project", description="Test", tags=["qa"])

        # Verify project object
        assert proj.name == "QA-Test-Project"
        assert proj.description == "Test"
        assert proj.tags == ["qa"]

        # Verify directories exist
        proj_dir = tmp_data_dir / "QA-Test-Project"
        assert proj_dir.exists()
        assert (proj_dir / "captures").exists()
        assert (proj_dir / "notes").exists()

    def test_create_project_persisted_in_json(self, pm, tmp_data_dir):
        pm.create("QA-Test-Project")
        projects_json = tmp_data_dir / "projects.json"
        assert projects_json.exists()
        data = json.loads(projects_json.read_text(encoding="utf-8"))
        assert "QA-Test-Project" in data

    def test_create_duplicate_raises(self, pm):
        pm.create("QA-Test-Project")
        with pytest.raises(ValueError):
            pm.create("QA-Test-Project")

    def test_create_empty_name_raises(self, pm):
        with pytest.raises(ValueError):
            pm.create("")


class TestTextCapture:
    """Test 2: Capture text into the project, verify file saved and metadata."""

    def test_capture_text_creates_file(self, project, tmp_data_dir):
        notes_dir = tmp_data_dir / project.name / "notes"
        text = "This is a QA test note with important content."
        filepath = capture_text(notes_dir, text, description="QA note")

        assert filepath.exists()
        assert filepath.read_text(encoding="utf-8") == text

    def test_capture_text_metadata(self, project, tmp_data_dir):
        notes_dir = tmp_data_dir / project.name / "notes"
        capture_text(notes_dir, "Test content", description="QA note")

        meta_path = notes_dir / "metadata.json"
        assert meta_path.exists()
        meta = json.loads(meta_path.read_text(encoding="utf-8"))
        assert len(meta) == 1
        assert meta[0]["type"] == "text"
        assert meta[0]["description"] == "QA note"

    def test_capture_empty_text_raises(self, project, tmp_data_dir):
        notes_dir = tmp_data_dir / project.name / "notes"
        with pytest.raises(ValueError):
            capture_text(notes_dir, "")


class TestPdfCapture:
    """Test 3: Create a test PDF, capture it, verify text extraction."""

    def test_capture_pdf(self, project, tmp_data_dir, tmp_path):
        import fitz
        # Create a test PDF with text
        pdf_path = tmp_path / "test_document.pdf"
        doc = fitz.open()
        page = doc.new_page()
        page.insert_text((72, 72), "Hello from QA test PDF document!")
        doc.save(str(pdf_path))
        doc.close()

        captures_dir = tmp_data_dir / project.name / "captures"
        notes_dir = tmp_data_dir / project.name / "notes"

        pdf_copy, txt_extract = capture_pdf(captures_dir, notes_dir, pdf_path, description="Test PDF")

        # Verify PDF was copied
        assert pdf_copy.exists()
        assert pdf_copy.suffix == ".pdf"

        # Verify text extraction worked
        assert txt_extract.exists()
        extracted = txt_extract.read_text(encoding="utf-8")
        assert "Hello from QA test PDF document!" in extracted

        # Verify metadata in both captures and notes
        cap_meta = json.loads((captures_dir / "metadata.json").read_text(encoding="utf-8"))
        assert any(m["type"] == "pdf" for m in cap_meta)

        notes_meta = json.loads((notes_dir / "metadata.json").read_text(encoding="utf-8"))
        assert any(m["type"] == "pdf_extract" for m in notes_meta)

    def test_capture_pdf_missing_file_raises(self, project, tmp_data_dir):
        captures_dir = tmp_data_dir / project.name / "captures"
        notes_dir = tmp_data_dir / project.name / "notes"
        with pytest.raises(FileNotFoundError):
            capture_pdf(captures_dir, notes_dir, Path("/nonexistent.pdf"))


class TestFileCapture:
    """Test 4: Copy a file into the project, verify it's there."""

    def test_capture_file(self, project, tmp_data_dir, tmp_path):
        # Create a test file
        src_file = tmp_path / "testfile.dat"
        src_file.write_text("binary-like content here", encoding="utf-8")

        captures_dir = tmp_data_dir / project.name / "captures"
        copied = capture_file(captures_dir, src_file, description="Test file capture")

        assert copied.exists()
        assert copied.read_text(encoding="utf-8") == "binary-like content here"
        assert "testfile" in copied.stem

        # Check metadata
        meta = json.loads((captures_dir / "metadata.json").read_text(encoding="utf-8"))
        assert any(m["type"] == "file" and m["original_name"] == "testfile.dat" for m in meta)

    def test_capture_missing_file_raises(self, project, tmp_data_dir):
        captures_dir = tmp_data_dir / project.name / "captures"
        with pytest.raises(FileNotFoundError):
            capture_file(captures_dir, Path("/nonexistent_file.xyz"))


class TestContextMdGeneration:
    """Test 5: After captures, verify context.md contains all expected sections."""

    def test_context_md_has_all_sections(self, project, tmp_data_dir, tmp_path):
        proj_dir = tmp_data_dir / project.name
        captures_dir = proj_dir / "captures"
        notes_dir = proj_dir / "notes"

        # Simulate some captures
        capture_text(notes_dir, "Important meeting notes", description="Meeting notes")

        # Create and capture a PDF
        import fitz
        pdf_path = tmp_path / "report.pdf"
        doc = fitz.open()
        page = doc.new_page()
        page.insert_text((72, 72), "Quarterly report content")
        doc.save(str(pdf_path))
        doc.close()
        capture_pdf(captures_dir, notes_dir, pdf_path, description="Q4 Report")

        # Capture a regular file
        data_file = tmp_path / "data.csv"
        data_file.write_text("col1,col2\n1,2\n", encoding="utf-8")
        capture_file(captures_dir, data_file, description="Test data")

        # Generate context.md
        md_path = generate_context_md(
            project.name, proj_dir,
            description=project.description,
            created_at=project.created_at,
        )

        assert md_path.exists()
        content = md_path.read_text(encoding="utf-8")

        # Verify all expected sections
        assert "# 프로젝트: QA-Test-Project" in content  # Header
        assert "## 개요" in content                       # Overview
        assert "## 타임라인" in content                    # Timeline
        assert "## 문서 내용 (PDF 추출)" in content       # PDF extract
        assert "## 텍스트 노트" in content                 # Text notes
        assert "## 파일 목록" in content                   # File list

        # Verify content details
        assert "Meeting notes" in content
        assert "Quarterly report content" in content
        assert "data.csv" in content


class TestDownloadsWatcher:
    """Test 6: Test the FileWatcher directly (no GUI)."""

    def test_watcher_detects_new_file(self, tmp_path):
        watch_dir = tmp_path / "fake_downloads"
        watch_dir.mkdir()

        detected_files = []
        event = threading.Event()

        def on_new_file(path: Path):
            detected_files.append(path)
            event.set()

        watcher = FileWatcher(callback=on_new_file, watch_dir=watch_dir, debounce_sec=0.3)
        watcher.start()
        assert watcher.is_running

        try:
            # Create a supported file
            test_file = watch_dir / "downloaded_report.pdf"
            test_file.write_text("fake pdf content", encoding="utf-8")

            # Wait for debounce + processing
            event.wait(timeout=5)

            assert len(detected_files) >= 1
            assert detected_files[0].name == "downloaded_report.pdf"
        finally:
            watcher.stop()

        assert not watcher.is_running

    def test_watcher_ignores_tmp_files(self, tmp_path):
        watch_dir = tmp_path / "fake_downloads"
        watch_dir.mkdir()

        detected_files = []

        def on_new_file(path: Path):
            detected_files.append(path)

        watcher = FileWatcher(callback=on_new_file, watch_dir=watch_dir, debounce_sec=0.3)
        watcher.start()

        try:
            # Create an ignored file type
            tmp_file = watch_dir / "partial.crdownload"
            tmp_file.write_text("downloading...", encoding="utf-8")

            time.sleep(1.5)
            assert len(detected_files) == 0
        finally:
            watcher.stop()


class TestScreenshotCapture:
    """Test 7: Test screenshot with mocked mss (no display required)."""

    def test_capture_screenshot_mocked(self, project, tmp_data_dir):
        captures_dir = tmp_data_dir / project.name / "captures"

        # Create a fake screenshot image bytes (10x10 red image)
        from PIL import Image
        import io

        fake_img = Image.new("RGB", (10, 10), color=(255, 0, 0))

        # Mock mss to return our fake data
        class FakeScreenshot:
            size = (10, 10)
            bgra = b'\x00\x00\xff\xff' * 100  # 10x10 BGRX pixels (red)

        class FakeSct:
            monitors = [{"left": 0, "top": 0, "width": 10, "height": 10}]

            def grab(self, monitor):
                return FakeScreenshot()

            def __enter__(self):
                return self

            def __exit__(self, *args):
                pass

        with patch("src.capture.mss.mss", return_value=FakeSct()):
            filepath = capture_screenshot(captures_dir, description="Test screenshot")

        assert filepath.exists()
        assert filepath.suffix == ".png"

        # Verify it's a valid image
        img = Image.open(filepath)
        assert img.size == (10, 10)

        # Check metadata
        meta = json.loads((captures_dir / "metadata.json").read_text(encoding="utf-8"))
        assert any(m["type"] == "screenshot" for m in meta)


class TestProjectPersistence:
    """Test 8: Create project, reload ProjectManager, verify project still exists."""

    def test_persistence_across_reload(self, tmp_data_dir):
        # Create project with first manager
        pm1 = ProjectManager(data_dir=tmp_data_dir)
        pm1.create("Persistent-Project", description="Should survive reload", tags=["persist"])

        # Create a completely new manager pointing to same dir
        pm2 = ProjectManager(data_dir=tmp_data_dir)
        assert pm2.exists("Persistent-Project")

        proj = pm2.get("Persistent-Project")
        assert proj.description == "Should survive reload"
        assert proj.tags == ["persist"]

    def test_persistence_with_captures(self, tmp_data_dir):
        pm1 = ProjectManager(data_dir=tmp_data_dir)
        proj = pm1.create("Data-Project")
        notes_dir = tmp_data_dir / proj.name / "notes"
        capture_text(notes_dir, "Persistent note", description="Test")

        # Reload and verify data files still there
        pm2 = ProjectManager(data_dir=tmp_data_dir)
        assert pm2.exists("Data-Project")
        notes = list((tmp_data_dir / "Data-Project" / "notes").glob("*.txt"))
        assert len(notes) == 1


class TestSendToInstallation:
    """Test 9: Verify the bat file can be created in SendTo folder."""

    def test_install_sendto_bat(self, tmp_path):
        """Test SendTo installation using a temp directory."""
        fake_sendto = tmp_path / "SendTo"
        fake_sendto.mkdir()

        with patch("src.sendto.SENDTO_DIR", fake_sendto):
            with patch("src.sendto.get_sendto_path", return_value=fake_sendto / "Clickary.lnk"):
                result = install_sendto()

        # Should have created the bat file (fallback since winshell likely not installed)
        bat_path = fake_sendto / "Clickary.bat"
        assert bat_path.exists()
        content = bat_path.read_text(encoding="utf-8")
        assert "sendto_handler.py" in content

    def test_real_sendto_dir_exists(self):
        """Verify the SendTo directory exists on this Windows system."""
        assert SENDTO_DIR.exists()


class TestAutostartRegistration:
    """Test 10: Verify the bat file for autostart."""

    def test_register_autostart_bat(self, tmp_path):
        """Test autostart registration using a temp directory."""
        fake_startup = tmp_path / "Startup"
        fake_startup.mkdir()
        fake_bat_path = fake_startup / "Clickary.bat"

        with patch("src.autostart.get_startup_path", return_value=fake_bat_path):
            result = register_autostart()

        assert result is True
        assert fake_bat_path.exists()
        content = fake_bat_path.read_text(encoding="utf-8")
        assert "src.main" in content

    def test_unregister_autostart(self, tmp_path):
        """Test autostart removal."""
        fake_startup = tmp_path / "Startup"
        fake_startup.mkdir()
        fake_bat_path = fake_startup / "Clickary.bat"
        fake_bat_path.write_text("dummy", encoding="utf-8")

        with patch("src.autostart.get_startup_path", return_value=fake_bat_path):
            result = unregister_autostart()

        assert result is True
        assert not fake_bat_path.exists()
