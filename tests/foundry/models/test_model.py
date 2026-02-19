import pytest
from django.db import models

# A concrete model for testing the abstract Model
from tests.testcase import TestCase

class TestModelClass(TestCase):
    @pytest.fixture(autouse=True)
    def set_model(self, django_test_environment):
        # Import the Queryset_Filter module after Django is set up
        global Model, TestModel
        from djangofoundry.models import Model as FoundryModel
        Model = FoundryModel

        class TestModel(Model):
            name = models.CharField(max_length=100)
            class Meta:
                app_label = "tests"

    @pytest.fixture
    def test_model(self):
        return TestModel(name="Test")

    def test_get_name(self, test_model):
        assert test_model.get_name() == "test model"

    def test_get_plural_name(self, test_model):
        assert test_model.get_plural_name() == "test models"

    def test_to_dict(self, test_model):
        test_model.id = 1
        assert test_model.to_dict() == {"id": 1, "name": "Test"}

    def test_presave(self, mock_save, test_model):
        # patch TestModel.save()
        test_model.save = mock_save

        test_model.presave()
        assert mock_save.called

    def test_get_field_column(self, test_model):
        assert test_model.get_field_column("name") == "name"

    def test_get_related_models(self, test_model):
        assert test_model.get_related_models() == []

    def test_str(self, test_model):
        test_model.id = 1
        assert str(test_model) == "test model 1"

    def test_repr(self, test_model):
        test_model.id = 1
        assert repr(test_model) == "{'id': 1, 'name': 'Test'}"
