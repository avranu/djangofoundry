import pytest
from unittest.mock import patch
from rest_framework.test import APIRequestFactory, force_authenticate
from .baker_recipes import TestViewSet
from tests.testcase import TestCase

class TestViewSetClass(TestCase):

    @pytest.fixture
    def viewset(self):
        return TestViewSet()

    @patch("djangofoundry.scripts.viewset.ReadOnlyModelViewSet.get_queryset")
    @patch.object(TestViewSet, 'apply_filters')
    def test_get_queryset(self, mock_apply_filters, mock_get_queryset, viewset):
        mock_get_queryset.return_value = "queryset"
        mock_apply_filters.return_value = "filtered queryset"
        result = viewset.get_queryset()
        assert result == "filtered queryset"

    @patch("djangofoundry.scripts.viewset.QuerySet.filter")
    def test_apply_filters(self, mock_filter, viewset):
        mock_filter.return_value = "filtered queryset"
        request = APIRequestFactory().get("/?test=1")
        force_authenticate(request)
        viewset.request = request
        viewset.filterset_fields = ["test"]
        queryset = "queryset"
        result = viewset.apply_filters(queryset)
        assert result == "filtered queryset"
