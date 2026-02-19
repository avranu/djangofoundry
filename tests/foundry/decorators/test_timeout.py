"""

    Metadata:

        File: test_timeout.py
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

'''
from djangofoundry.decorators.timeout import timeout
class TimeoutTestCase(TestCase):
    def test_timeout_decorator(self):
        @timeout(1)
        def sample_function():
            sleep(2)
            return "Function completed"

        @timeout(3)
        def another_function():
            sleep(1)
            return "Another function completed"

        with self.assertRaises(TimeoutError):
            sample_function()

        result = another_function()
        self.assertEqual(result, "Another function completed")
'''