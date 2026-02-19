"""


    Metadata:

        File: Choices.py
        Project: Django Foundry
        Created Date: 31 Aug 2022
        Author: Jess Mann
        Email: jess.a.mann@gmail.com

        -----

        Last Modified: Sat Dec 03 2022
        Modified By: Jess Mann

        -----

        Copyright (c) 2022 Jess Mann

"""
# Generic imports
from __future__ import annotations

# Django imports
from django.test import TestCase
# Lib imports
from djangofoundry.models.choices import TextChoices
# App imports

class ChoicesTest(TestCase):

    def setUp(self):
        pass

    def test_choices_valid(self):
        class Choices(TextChoices):
            FOO = 'Foo'
            BAR = 'Notbar'

        assert Choices.valid('foo') is True, "TextChoices.valid() not working in simplest case."
        assert Choices.valid('FOo') is True, "TextChoices.valid() not normalizing capitalization"
        assert Choices.valid('notbar') is True, "TextChoices.valid() not working for choice with different label."
        assert Choices.valid('bing') is False, "TextChoices.valid() not failing for missing values"
        assert Choices.valid('BAR') is False, "TextChoices.valid() is accepting variable names instead of labels"

        assert Choices.invalid('bar') is True, "TextChoices.invalid() accepting variable names instead of labels"
        assert Choices.invalid('BAR') is True, "TextChoices.invalid() accepting variable names with full capitalization"
        assert Choices.invalid('foo') is False, "TextChoices.invalid() not working in simplest case."
        assert Choices.invalid('FoO') is False, "TextChoices.invalid() not normalizing capitalization"
        assert Choices.invalid('bing') is True, "TextChoices.invalid() not failing for missing values"