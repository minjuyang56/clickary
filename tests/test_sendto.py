"""sendto 모듈 테스트."""

from pathlib import Path
from unittest.mock import patch

from src.sendto import get_sendto_path, is_installed, SENDTO_DIR


class TestSendTo:
    """Send To 기능 테스트."""

    def test_get_sendto_path(self):
        """바로가기 경로 확인."""
        path = get_sendto_path()
        assert path.name == "Clickary.lnk"
        assert "SendTo" in str(path)

    def test_is_installed_false(self):
        """설치되지 않은 상태."""
        with patch.object(Path, "exists", return_value=False):
            assert not is_installed()

    def test_sendto_dir_exists(self):
        """SendTo 디렉토리 존재 확인."""
        assert SENDTO_DIR.exists()
