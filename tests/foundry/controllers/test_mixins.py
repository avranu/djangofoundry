"""

    Metadata:

        File: mixins.py
        Project: Django Foundry
        Created Date: 15 Sep 2022
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
from django.views import View
# Lib imports
from djangofoundry.mixins import HasParams
# App imports

class Sample(HasParams, View):
    pass

class HasParamsTest(TestCase):

    def setUp(self):
        self.sample = Sample()

        # user input => expected value (True means unchanged, False means raises error)
        self.str_inputs = {
            'basic': 	 			True,
            'with spaces': 			'withspaces',
            '   with  spa ces  ': 	'withspaces',
            '123': 					True,
            'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_': True,
            '!@#$%^&*()[{]};:\'",<.>/\\|?`~- 	': ',-',
        }

        self.int_inputs = {
            'basic': 	 			False,
            'with spaces': 			False,
            '   with  spa ces  ': 	False,
            '123': 					123,
            'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_': 123456789,
            '!@#$%^&*()[{]};:\'",<.>/\\|?`~- 	': False,
        }

    def test_sanitize_str(self):
        for (input, output) in self.str_inputs.items():
            if output is False:
                with self.assertRaises(Exception, msg=f"Sanitize str ({input}) did not throw exception."):
                    self.sample.sanitize_str(input)
            else:
                if output is True:
                    output = input
                result = self.sample.sanitize_str(input)
                self.assertEquals(output, result, msg=f"Sanitize str failed: ({input}) => ({result}), expected ({output})")

    def test_sanitize_int(self):
        for (input, output) in self.int_inputs.items():
            if output is False:
                with self.assertRaises(ValueError, msg=f"Sanitize int ({input}) did not throw exception."):
                    self.sample.sanitize_int(input)
            else:
                if output is True:
                    output = input
                result = self.sample.sanitize_int(input)
                self.assertEquals(output, result, msg=f"Sanitize int failed: ({input}) => ({result}), expected ({output})")