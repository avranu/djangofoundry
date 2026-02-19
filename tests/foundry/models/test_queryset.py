"""

    Metadata:

        File: test_queryset.py
        Project: Django Foundry
        Created Date: 09 Apr 2023
        Author: Jess Mann
        Email: jess.a.mann@gmail.com

        -----

        Last Modified: Wed May 10 2023
        Modified By: Jess Mann

        -----

        Copyright (c) 2023 Jess Mann
"""
from math import sqrt
from django.test import TestCase
from model_bakery import baker
import pytest

class QuerySetTestPerson(TestCase):
    app = 'django-foundry'
    case_attributes : list[dict]
    person_attributes : list[dict]

    @pytest.fixture(autouse=True)
    def import_django(self, django_test_environment):
        # Import code that relies on django after Django is set up
        global Person, PersonQS, Case, CaseQS, QuerySet, Manager
        from djangofoundry import models
        from . import baker_recipes as recipes

        QuerySet = models.QuerySet
        Manager = models.Manager
        Person = recipes.Person
        PersonQS = recipes.PersonQS
        Case = recipes.Case
        CaseQS = recipes.CaseQS

        # Store case attributes in a dict so we can reference them in tests.
        self.case_attributes = [
            {
                'case_type': 'test_case_1',
                'case_id': 5,
                'summary': 'test',
                'category': 'value1',
            },
            {
                'case_type': 'test_case_2',
                'case_id': 100,
                'summary': 'test2',
                'category': 'value2',
            },
            {
                'case_type': 'test_case_3',
                'case_id': -5,
                'summary': '',
                'category': 'value_3',
                'status': 'open',
                'processing_ms': 9,
            },
            {
                'case_type': 'test_case_4',
                'status': 'open',
                'location': '10023',
                'processing_ms': 1,
                'summary': None,
            },
            {
                'case_type': 'test_case_5',
                'status': 'closed',
                'location': '52312',
                'processing_ms': 2,
            },
            {
                'case_type': 'test_case_6',
                'status': '',
                'location': '',
                'processing_ms': 3,
            }
        ]

        self.cases = []
        for attribs in self.case_attributes:
            model = baker.make(Case, **attribs)
            self.cases.append(model)

    def _create_sample_cases(self):
        # Create a list of cases to test with
        cases = []
        for attribs in self.case_attributes:
            cases.append(Case(**attribs))
        return cases

    def _create_sample_people(self):
        # Create a list of people to test with.
        people = []
        for i in range(100):
            people.append(Person(age=i))
        return people

    def test_is_evaluated(self):
        qs = Case.objects.all()
        self.assertFalse(qs.is_evaluated())
        list(qs)
        self.assertTrue(qs.is_evaluated())

    def test_field_is_numeric(self):
        self.assertTrue(Case.objects.field_is_numeric("case_id"))
        self.assertFalse(Case.objects.field_is_numeric("summary"))

    def test_latest_value(self):
        latest_value = Case.objects.latest_value("category")
        self.assertEqual(latest_value, self.cases[-1].category)

    def test_has_smallest(self):
        qs = Case.objects.has_smallest("id")
        self.assertTrue(qs.exists())
        self.assertEqual(qs.first().id, 1)

    def test_has_largest(self):
        qs = Case.objects.has_largest("id")
        self.assertTrue(qs.exists())
        self.assertEqual(qs.first().id, self.cases[-1].case_id)

    def test_has_blank(self):
        qs = Case.objects.has_blank("summary", include_null=False)
        self.assertTrue(qs.exists())
        for model in qs:
            self.assertEqual(model.summary, '')
        self.assertEqual(qs.count(), 1)

    def test_has_blank_or_null(self):
        qs = Case.objects.has_blank("summary", include_null=True)
        self.assertTrue(qs.exists())
        for model in qs:
            # assert it is a blank string or null
            self.assertTrue(model.summary == '' or model.summary is None)
        self.assertEqual(qs.count(), 4)

    def test_have_blanks(self):
        qs = Case.objects.have_blanks(number_of_blank_fields=1, include_null=False)
        self.assertTrue(qs.exists())
        for model in qs:
            # test that at least one field of the property (any field) is blank
            blank = False
            for field in model._meta.get_fields():
                if getattr(model, field.name) == '':
                    blank = True
                    break
            self.assertTrue(blank)
        self.assertEqual(qs.count(), 2)

    def test_have_multiple_blanks(self):
        total_blanks = 2
        qs = Case.objects.have_blanks(number_of_blank_fields=total_blanks, include_null=False)
        self.assertTrue(qs.exists())
        for model in qs:
            # count the blanks
            blank_count = 0
            for field in model._meta.get_fields():
                if getattr(model, field.name) == '':
                    blank_count += 1
            self.assertEqual(blank_count, total_blanks)
        self.assertEqual(qs.count(), 1)

    def test_total(self):
        total = Case.objects.total("case_id")
        # sum the values of all case_id
        expected_total = 0
        for model in self.cases:
            expected_total += model.case_id

        self.assertEqual(total, expected_total)

    def test_request(self):
        # Register a filter for testing
        def example_filter(queryset):
            return queryset.filter(category="value1")

        QuerySet.filters["example_filter"] = example_filter

        qs = Case.objects.request("example_filter")
        self.assertTrue(qs.exists())
        self.assertEqual(qs.first().category, self.cases[0].category)

    def test_apply_filter(self):
        # Register a filter for testing
        def example_filter(queryset):
            return queryset.filter(category="value1")

        QuerySet.filters["example_filter"] = example_filter

        qs = Case.objects.apply_filter("example_filter")
        self.assertTrue(qs.exists())
        self.assertEqual(qs.first().category, self.cases[0].category)

    def test_apply_filter_raises_error(self):
        with self.assertRaises(NotImplementedError):
            Case.objects.apply_filter("non_existent_filter")

    def test_group_report(self):
        result = Case.objects.group_report('status')
        expected_result = {'open': 2, 'closed': 1}
        self.assertEqual(result, expected_result)

    def test_group_total(self):
        result = Case.objects.group_total('status', 'open')
        self.assertEqual(result, 10)
        result = Case.objects.group_total('status', 'closed')
        self.assertEqual(result, 1)

    def test_summarize_x_by_average_y(self):
        result = Case.objects.summarize_x_by_average_y('status', 'processing_time')
        expected_result = {'open': 5.0, 'closed': 1.0}
        self.assertEqual(result, expected_result)

    def test_summarize_x_by_sum_y(self):
        result = Case.objects.summarize_x_by_sum_y('status', 'processing_time')
        expected_result = {'open': 10.0, 'closed': 1.0}
        self.assertEqual(result, expected_result)

    def test_summarize_x_by_high_y(self):
        cases = self._create_sample_cases()
        result = Case.objects.summarize_x_by_high_y('status', 'processing_time')
        expected_result = {'open': 1, 'closed': 0}
        self.assertEqual(result, expected_result)

    def test_summarize_x_by_low_y(self):
        cases = self._create_sample_cases()
        result = Case.objects.summarize_x_by_low_y('status', 'processing_time')
        expected_result = {'open': 0, 'closed': 1}
        self.assertEqual(result, expected_result)

    def test_anomalies_in(self):
        cases = self._create_sample_cases()
        result = Case.objects.anomalies_in('processing_time', deviations=1)
        self.assertEqual(len(result), 1)
        self.assertCountEqual(result, [cases[1]])

    def test_summarize_distribution(self):
        cases = self._create_sample_cases()
        result = Case.objects.summarize_distribution('processing_time', bins=5)
        expected_result = {0: 1, 1: 1, 2: 1, 3: 0, 4: 0}
        self.assertEqual(result, expected_result)

    def test_summarize_x_by_y_distribution(self):
        cases = self._create_sample_cases()
        result = Case.objects.summarize_x_by_y_distribution('status', 'processing_time', bins=5)
        expected_result = {
            'open': {0: 1, 1: 0, 2: 1, 3: 0, 4: 0},
            'closed': {0: 0, 1: 1, 2: 0, 3: 0, 4: 0}
        }
        self.assertEqual(result, expected_result)

    def test_count_unique(self):
        cases = self._create_sample_cases()
        result = Case.objects.count_unique('status')
        self.assertEqual(result, 2)

    def test_count_x_by_unique_y(self):
        expected = {'open': 1, 'closed': 0}
        actual = Case.objects.count_x_by_unique_y('status', 'location')
        self.assertEqual(actual, expected)

    def test_median(self):
        expected = 2.5
        actual = Case.objects.median('processing_time')
        self.assertAlmostEqual(actual, expected)

    def test_percentile(self):
        expected = 2
        actual = Case.objects.percentile('processing_time', 0.5)
        self.assertEqual(actual, expected)

    def test_mode(self):
        expected = 'open'
        actual = Case.objects.mode('status')
        self.assertEqual(actual, expected)

    def test_variance(self):
        expected = 1.25
        actual = Case.objects.variance('processing_time')
        self.assertAlmostEqual(actual, expected)

    def test_standard_deviation(self):
        expected = sqrt(1.25)
        actual = Case.objects.standard_deviation('processing_time')
        self.assertAlmostEqual(actual, expected)

    def test_covariance(self):
        expected = 1.25
        actual = Case.objects.covariance('processing_time', 'processing_time')
        self.assertAlmostEqual(actual, expected)

    def test_correlation(self):
        expected = 1.0
        actual = Case.objects.correlation('processing_time', 'processing_time')
        self.assertAlmostEqual(actual, expected)

    def test_linear_regression(self):
        expected = (0.0, 1.0)
        actual = Case.objects.linear_regression('processing_time', 'processing_time')
        self.assertAlmostEqual(actual[0], expected[0])
        self.assertAlmostEqual(actual[1], expected[1])
