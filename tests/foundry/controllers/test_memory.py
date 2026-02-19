import pytest
from unittest.mock import patch
from django.http import HttpRequest
from djangofoundry.controllers.memory import MemoryMonitorView, memory_usage

from tests.testcase import TestCase

class TestMemoryMonitorView(TestCase):

    @pytest.fixture
    def memory_monitor_view(self):
        return MemoryMonitorView()

    def test_get(self, memory_monitor_view):
        request = HttpRequest()
        response = memory_monitor_view.get(request)
        assert response.status_code == 200
        assert 'memory.html' in response.template_name

from tests.testcase import TestCase

class TestMemoryUsage(TestCase):

    @patch('psutil.Process')
    @patch('psutil.process_iter')
    @patch('psutil.virtual_memory')
    @patch('psutil.cpu_percent')
    @patch('tracemalloc.start')
    @patch('tracemalloc.take_snapshot')
    def test_memory_usage(self, mock_snapshot, mock_cpu_percent, mock_virtual_memory, mock_process_iter, mock_process):
        request = HttpRequest()
        response = memory_usage(request)
        assert response.status_code == 200
