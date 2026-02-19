from django.db.models import Model, CharField, IntegerField
from rest_framework import serializers
from djangofoundry.models import QuerySet, Manager
from djangofoundry.models.serializer import Serializer
from djangofoundry.models.viewset import ViewSet

class TestModel(Model):
    name = CharField(max_length=100)
    class Meta:
        app_label = "tests"

class PersonQS(QuerySet):
    def over_18(self) -> QuerySet:
        return self.filter(age__gte=18)

class Person(Model):
    age = IntegerField()
    objects = Manager.from_queryset(PersonQS)()

    class Meta:
        app_label = 'django-foundry'

class CaseQS(QuerySet):
    def category(self, category : str) -> QuerySet:
        return self.filter(category=category)
    def location(self, location : str) -> QuerySet:
        return self.filter(location=location)

class Case(Model):
    case_type = CharField(max_length=100)
    case_id = IntegerField()
    summary = CharField(max_length=100)
    category = CharField(max_length=100)
    status = CharField(max_length=100)
    location = CharField(max_length=100)
    processing_ms = IntegerField()

    objects = Manager.from_queryset(CaseQS)()

    class Meta:
        app_label = 'django-foundry'

class TestSerializer(Serializer):
    id = serializers.IntegerField()
    name = serializers.CharField()

    class Meta:
        fields = ['id', 'name']
        generated_fields = ['name']

class TestViewSet(ViewSet):
    serializer_class = Serializer