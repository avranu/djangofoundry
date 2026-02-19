import pytest
from unittest.mock import MagicMock
from tests.testcase import TestCase

class TestQuerysetFilter(TestCase):

    @pytest.fixture(autouse=True)
    def set_queryset_filter(self, django_test_environment):
        # Import the Queryset_Filter module after Django is set up
        global Queryset_Filter
        from djangofoundry.decorators.queryset_filter import Queryset_Filter as QF
        Queryset_Filter = QF

    def test_init(self):
        def filter_fn():
            return "filter result"
        queryset_filter = Queryset_Filter(filter_fn, "test_filter")
        assert queryset_filter.filter_fn == filter_fn
        assert queryset_filter.name == "test_filter"

    def test_set_name(self):
        def filter_fn():
            return "filter result"

        queryset_filter = Queryset_Filter(filter_fn, "test_filter")
        queryset_filter.__set_name__(MagicMock(filters={}), "test_filter")
        assert "test_filter" in queryset_filter.queryset.filters

    def test_get(self):
        def filter_fn():
            return "filter result"
        queryset_filter = Queryset_Filter(filter_fn, "test_filter")
        queryset_filter.__get__(None, MagicMock())
        assert queryset_filter.queryset is None

    def test_call(self):
        def filter_fn(*args, **kwargs):
            return "filter result"
        queryset_filter = Queryset_Filter(filter_fn, "test_filter")
        result = queryset_filter(1, 2, 3, test="test")
        assert result == "filter result"
