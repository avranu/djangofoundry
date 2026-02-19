import pytest
from unittest.mock import patch, MagicMock
from djangofoundry.scripts.app import App
import psutil
import subprocess

from tests.testcase import TestCase

class TestApp(TestCase):

    @pytest.fixture
    def app(self):
        return App('test_project', 'test_author', {}, '/test_dir', 'frontend', 'backend')

    def test_app_init(self, app):
        assert app.project_name == 'test_project'
        assert app.author_name == 'test_author'
        assert app.settings == {}
        assert app.directory == '/test_dir'
        assert app.frontend_dir == 'frontend'
        assert app.backend_dir == 'backend'

    @patch('os.makedirs')
    @patch.object(App, 'check_environment')
    @patch.object(App, 'create_venv')
    @patch.object(App, 'install_dependencies')
    @patch.object(App, 'django_setup')
    @patch.object(App, 'nuxt_setup')
    @patch.object(App, 'confirm_setup')
    def test_app_setup(self, confirm_setup, nuxt_setup, django_setup, install_dependencies, create_venv, check_environment, makedirs, app):
        app.setup()
        makedirs.assert_called_once_with('/test_dir', exist_ok=True)
        check_environment.assert_called_once()
        create_venv.assert_called_once()
        install_dependencies.assert_called_once()
        django_setup.assert_called_once()
        nuxt_setup.assert_called_once()
        confirm_setup.assert_called_once()

    @patch.object(psutil, 'disk_usage')
    @patch.object(psutil, 'virtual_memory')
    @patch('os.access')
    @patch('sys.version_info')
    def test_check_environment(self, mock_version_info, mock_access, mock_ram_usage, mock_disk_usage, app):
        # Mocking the system environment checks
        mock_version_info.__getitem__.side_effect = [3, 10]
        mock_access.return_value = True
        mock_disk_usage.return_value = MagicMock(free=10**10)
        mock_ram_usage.return_value = MagicMock(available=10**10)
        app.check_environment()

    @patch.object(subprocess, 'Popen')
    def test_run_subprocess(self, mock_popen, app):
        mock_popen.return_value.__enter__.return_value.stdout = iter(["output"])
        app.run_subprocess(['ls'])
        mock_popen.assert_called_once_with(['ls'], stdout=subprocess.PIPE, encoding="utf-8")
