"""

    Metadata:

        File: test_hooks.py
        Project: Django Foundry
        Created Date: 30 Apr 2023
        Author: Jess Mann
        Email: jess.a.mann@gmail.com

        -----

        Last Modified: Wed May 10 2023
        Modified By: Jess Mann

        -----

        Copyright (c) 2023 Jess Mann
"""
from django.test import TestCase
from djangofoundry.helpers.hooks.meta.types import WaypointMap
from djangofoundry.helpers.hooks.waypoint import Waypoint
from djangofoundry.helpers.hooks.hook import Hook, DEFAULT_NAMESPACE, DEFAULT_PRIORITY

from tests.testcase import TestCase

class TestHook(TestCase)(TestCase):

    def setUp(self):
        self.action = lambda x: x * 2
        self.hook = Hook("test_hook", self.action)

    def test_hook_initialization(self):
        self.assertEqual(self.hook.namespace, DEFAULT_NAMESPACE)
        self.assertEqual(self.hook.name, "test_hook")
        self.assertEqual(self.hook.action, self.action)
        self.assertEqual(self.hook.priority, DEFAULT_PRIORITY)
        self.assertEqual(self.hook.max_executions, -1)

    '''
    def test_can_run(self):
        self.assertTrue(self.hook.can_run())
        limited_hook = Hook("limited_hook", self.action, max_executions=2)
        self.assertTrue(limited_hook.can_run())
        limited_hook.run(2)
        self.assertTrue(limited_hook.can_run())
        limited_hook.run(2)
        self.assertFalse(limited_hook.can_run())

    def test_run(self):
        execution_success, result = self.hook.run(2)
        self.assertTrue(execution_success)
        self.assertEqual(result, 4)
    '''

    def test_force_run(self):
        result = self.hook.force_run(2)
        self.assertEqual(result, 4)

    def test_max_executions_error(self):
        with self.assertRaises(ValueError):
            Hook("error_hook", self.action, max_executions=0)


'''
class WaypointTestCase(TestCase):

    def setUp(self):
        self.hook1 = Hook(priority=10, function=func1)
        self.hook2 = Hook(priority=20, function=func2)
        self.waypoint = WaypointMap(name='test_waypoint', hooks=[self.hook1, self.hook2])

    def test_invalid_positional_arguments(self):
        with self.assertRaises(ValueError):
            Waypoint(name='test_waypoint', positional_arguments=-1)

    def test_run(self):
        # Assuming func1 and func2 return appropriate data for the *args and **kwargs given.
        results = self.waypoint.run('arg1', 'arg2', some_key='some_value')
        self.assertIn(func1('arg1', 'arg2', some_key='some_value'), results)
        self.assertIn(func2('arg1', 'arg2', some_key='some_value'), results)

    def test_run_with_different_priorities(self):
        self.hook1.priority = 30
        self.waypoint.hooks.sort(key=lambda x: x.priority, reverse=True)
        results = self.waypoint.run('arg1', 'arg2', some_key='some_value')
        self.assertEqual(results, [func2('arg1', 'arg2', some_key='some_value'), func1('arg1', 'arg2', some_key='some_value')])
'''