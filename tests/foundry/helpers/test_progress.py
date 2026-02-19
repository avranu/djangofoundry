import pytest
from decimal import Decimal
from djangofoundry.helpers.progress import ProgressBar, ChildProgressBar

from tests.testcase import TestCase

class TestProgressBar(TestCase):

    @pytest.fixture
    def progress_bar(self):
        return ProgressBar(total=10)

    def test_init(self, progress_bar):
        assert progress_bar.total == 10
        assert progress_bar.current == 0
        assert progress_bar.description == ''
        assert progress_bar.pending == False
        assert progress_bar.percent == Decimal('0.0')

    def test_update(self, progress_bar):
        progress_bar.update(current=5, description='Halfway there', total=20)
        assert progress_bar.current == 5
        assert progress_bar.description == 'Halfway there'
        assert progress_bar.total == 20

    def test_advance(self, progress_bar):
        progress_bar.advance(3, 'A bit more')
        assert progress_bar.current == 3
        assert progress_bar.description == 'A bit more'

    def test_restart(self, progress_bar):
        progress_bar.restart(100, 'Restarted')
        assert progress_bar.current == 1
        assert progress_bar.description == 'Restarted'
        assert progress_bar.total == 100

from tests.testcase import TestCase

class TestChildProgressBar(TestCase):

    @pytest.fixture
    def child_progress_bar(self, progress_bar):
        return ChildProgressBar(parent=progress_bar, total=5, current=2)

    def test_init(self, child_progress_bar):
        assert child_progress_bar.total == 5
        assert child_progress_bar.current == 2
        assert child_progress_bar.parent is not None

    def test_update(self, child_progress_bar):
        child_progress_bar.update(4)
        assert child_progress_bar.current == 4
