import pytest
from unittest.mock import patch
from djangofoundry.scripts.build import PackageUploader

from tests.testcase import TestCase

class TestPackageUploader(TestCase):

    @pytest.fixture
    def mock_uploader(self):
        with patch.object(PackageUploader, 'load_config', return_value=None):
            return PackageUploader("test.toml")

    def test_init(self, mock_uploader):
        assert mock_uploader.toml_file == "test.toml"
        assert mock_uploader.config is None

    @patch("builtins.open")
    @patch("toml.load")
    def test_load_config(self, mock_toml_load, mock_open, mock_uploader):
        mock_toml_load.return_value = {"key": "value"}
        result = mock_uploader.load_config()
        assert result == {"key": "value"}

    @patch("builtins.open")
    @patch("toml.dump")
    def test_save_config(self, mock_toml_dump, mock_open, mock_uploader):
        mock_uploader.config = {"key": "value"}
        mock_uploader.save_config()
        mock_toml_dump.assert_called_once_with({"key": "value"}, mock_open.return_value.__enter__.return_value)

    @patch.object(PackageUploader, 'save_config')
    def test_update_minor_version(self, mock_save_config, mock_uploader):
        mock_uploader.config = {"tool": {"poetry": {"version": "1.0.0"}}}
        mock_uploader.update_minor_version()
        assert mock_uploader.config["tool"]["poetry"]["version"] == "1.1.0"

    @patch("subprocess.run")
    def test_build_package(self, mock_run, mock_uploader):
        mock_uploader.build_package()
        mock_run.assert_called_once_with(["python", "-m", "build"], check=True)
