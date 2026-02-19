import pytest
from unittest.mock import patch, MagicMock
from pathlib import Path
from djangofoundry.scripts.db import db, functions, Actions

from tests.testcase import TestCase

class TestDb(TestCase):
    @pytest.fixture
    def mock_db(self):
        # Initialize Db with test paths
        return db.Db(data_path="/test/data/path", log_path="/test/log/path")

    def test_init(self, mock_db):
        # Test __init__ method
        assert mock_db.data_path == "/test/data/path"
        assert mock_db.log_path == "/test/log/path"
        assert mock_db.user == "postgres"  # Default user
        assert mock_db.database == "DjangoFoundry"  # Default database

    @patch("os.path.isdir")
    @patch("os.path.isfile")
    @patch("shutil.which")
    def test_init_exception(self, mock_which, mock_isfile, mock_isdir):
        # Test __init__ method exceptions
        mock_isdir.return_value = False
        mock_isfile.return_value = False
        mock_which.return_value = None
        with pytest.raises(ValueError):
            db.Db(data_path="/nonexistent/data/path", log_path="/nonexistent/log/path")

    @patch("os.makedirs")
    def test_create_data_dir(self, mock_makedirs, mock_db):
        # Test create_data_dir method
        mock_db.data_path = "/nonexistent/data/path"
        mock_db.create_data_dir()
        mock_makedirs.assert_called_once_with("/nonexistent/data/path")

    @patch("os.path.isdir")
    @patch("shutil.move")
    def test_move_data_dir(self, mock_move, mock_isdir, mock_db):
        # Test move_data_dir method
        mock_isdir.return_value = True
        assert mock_db.move_data_dir("/new/data/path")
        mock_move.assert_called_once_with(mock_db.data_path, "/new/data/path")
        assert mock_db.data_path == "/new/data/path"



def test_get_app_dir():
    with patch('pathlib.Path.home', return_value=Path('/home/testuser')):
        result = functions.get_app_dir('data')
        assert result == Path('/home/testuser/postgres/data')

        result = functions.get_app_dir('logs')
        assert result == Path('/home/testuser/postgres/logs')

        with pytest.raises(ValueError):
            functions.get_app_dir('invalid')

@patch('functions.logger')
def test_db_action(mock_logger):
    test_func = MagicMock()

    # Test with a string action name
    decorated_func = functions.db_action('start')(test_func)
    mock_logger.debug.assert_called_once_with('Registering action: start to {}'.format(test_func))
    assert decorated_func == test_func
    assert functions.REGISTERED_ACTIONS['start'] == test_func

    mock_logger.reset_mock()
    test_func.reset_mock()

    # Test with an Actions enum value 
    decorated_func = functions.db_action(Actions.START)(test_func)
    mock_logger.debug.assert_called_once_with('Registering action: START ACTION to {}'.format(test_func))
    assert decorated_func == test_func
    assert functions.REGISTERED_ACTIONS['START'] == test_func
