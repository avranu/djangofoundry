import pytest
from unittest.mock import patch
from djangofoundry.scripts.utils.settings import Settings

from tests.testcase import TestCase

class TestSettings(TestCase):

    @pytest.fixture
    def mock_settings(self):
        with patch.object(Settings, 'load_config', return_value=None):
            return Settings()

    def test_init(self, mock_settings):
        assert mock_settings._settings is None
        assert mock_settings._logging_setup is False

    @patch("os.path.exists")
    @patch("yaml.load")
    def test_load_config(self, mock_yaml_load, mock_exists, mock_settings):
        mock_exists.return_value = True
        mock_yaml_load.return_value = {"key": "value"}
        result = mock_settings.load_config()
        assert result == {"key": "value"}

    def test_all(self, mock_settings):
        mock_settings._settings = {"key": "value"}
        result = mock_settings.all()
        assert result == {"key": "value"}

    def test_get(self, mock_settings):
        mock_settings._settings = {"key": "value"}
        result = mock_settings.get("key")
        assert result == "value"

    @patch("logging.config.dictConfig")
    @patch("logging.getLogger")
    def test_getLogger(self, mock_getLogger, mock_dictConfig, mock_settings):
        mock_getLogger.return_value = "Logger"
        mock_settings._logging_setup = False
        result = mock_settings.getLogger("namespace")
        assert result == "Logger"
        assert mock_settings._logging_setup == True
