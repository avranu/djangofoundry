import pytest
from unittest.mock import patch

from tests.testcase import TestCase

class TestRetry(TestCase):

    @pytest.fixture(autouse=True)
    def set_retry(self, django_test_environment):
        # Import the Queryset_Filter module after Django is set up
        global retry
        from djangofoundry.decorators.retry import retry as retry_decorator
        retry = retry_decorator

    def test_retry_success(self):
        # Function that always succeeds
        @retry(tries=5, delay=1, backoff=2)
        def test_func():
            return True
        assert test_func() == True

    def test_retry_failure(self):
        # Function that always fails
        @retry(tries=5, delay=1, backoff=2)
        def test_func():
            return False
        assert test_func() == False

    @patch('time.sleep', side_effect=InterruptedError)
    def test_retry_interrupted(self, mock_sleep):
        # Function that is interrupted
        @retry(tries=5, delay=1, backoff=2)
        def test_func():
            return False
        with pytest.raises(InterruptedError):
            test_func()

    def test_retry_invalid(self):
        with pytest.raises(ValueError):
            @retry(tries=-1, delay=1, backoff=2)
            def test_func():
                return True

        with pytest.raises(ValueError):
            @retry(tries=5, delay=0, backoff=2)
            def test_func():
                return True

        with pytest.raises(ValueError):
            @retry(tries=5, delay=1, backoff=1)
            def test_func():
                return True
