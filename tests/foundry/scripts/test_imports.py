import pytest
from unittest.mock import patch
from djangofoundry.scripts.imports import ImportProcessor

from tests.testcase import TestCase

class TestImportProcessor(TestCase):

    @pytest.fixture
    def mock_processor(self):
        return ImportProcessor("test_path")

    def test_init(self, mock_processor):
        assert mock_processor.path == "test_path"

    @patch("os.walk")
    @patch("builtins.open")
    @patch("re.search")
    def test_find_files_with_patterns(self, mock_search, mock_open, mock_walk, mock_processor):
        mock_walk.return_value = [("root", "dirs", ["test.py"])]
        mock_search.return_value = True
        result = mock_processor.find_files_with_patterns("pattern1", "pattern2")
        assert result == ["root/test.py"]

    @patch("builtins.open")
    @patch("re.findall")
    def test_find_imports(self, mock_findall, mock_open, mock_processor):
        mock_findall.return_value = ["import1", "import2"]
        result = mock_processor.find_imports("test.py")
        assert result == ["import1", "import2"]