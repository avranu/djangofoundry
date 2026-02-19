"""

    Metadata:

        File: test_queue.py
        Project: Django Foundry
        Created Date: 05 Sep 2022
        Author: Jess Mann
        Email: jess.a.mann@gmail.com

        -----

        Last Modified: Wed May 10 2023
        Modified By: Jess Mann

        -----

        Copyright (c) 2022 - 2023 Jess Mann
"""
# Generic imports
from __future__ import annotations

# Django imports
# Lib imports
# App imports

MAX_SIZE = 3

'''
class QueueTest(TestCase):

    @property
    def sample(self):
        # Create a new sample object to return
        return baker.make_recipe('dashboard_app.Person')

    def setUp(self):
        self.queue = Queue(limit=MAX_SIZE, unique_key='id')

    def _fill(self, size: int = MAX_SIZE):
        for i in range(size - self.queue.size()):
            sample = self.sample
            self.queue.append(sample)
        self.assertEquals(self.queue.size(), size)

    def _append(self, expected : int):
        result = self.queue.append(self.sample)
        self.assertIs(result, expected)
        self.assertIs(self.queue.size(), expected)

    def _expect(self, expected: int):
        self.assertEquals(self.queue.size(), expected)

    def test_size(self):
        self.assertEquals(self.queue.size(), 0)

        self.queue.queue.append(self.sample)
        self.assertEquals(self.queue.size(), 1)
        self.queue.queue.append(self.sample)
        self.assertEquals(self.queue.size(), 2)
        self.queue.queue.append(self.sample)
        self.queue.queue.append(self.sample)
        self.queue.queue.append(self.sample)
        self.queue.queue.append(self.sample)
        self.assertEquals(self.queue.size(), 6)
        self.queue.queue.pop()
        self.assertEquals(self.queue.size(), 5)
        self.queue.queue.append(self.sample)
        self.assertEquals(self.queue.size(), 6)
        self.queue.queue = deque()
        self.assertEquals(self.queue.size(), 0)
        self._fill(3)
        self.assertEquals(self.queue.size(), 3)

        count = 0
        person: Person
        for person in self.queue.queue:
            count += 1
            # Do something so there's no chance of python optimizing this loop away
            person.emplid = 5

        self.assertEquals(count, 3)
        self.assertEquals(self.queue.size(), 3)

    def test_append(self):
        # Starts off right
        self.assertEquals(self.queue.size(), 0)

        # Append works
        self.queue.append(self.sample)
        self.assertEquals(self.queue.size(), 1)
        self.queue.append(self.sample)
        self.assertEquals(self.queue.size(), 2)
        self.queue.append(self.sample)
        self.assertEquals(self.queue.size(), 3)


    def test_get(self):
        # Starts off right
        self.assertEquals(self.queue.size(), 0)
        self._fill(2)
        self.assertEquals(self.queue.size(), 2)
        self.queue.get()
        self.assertEquals(self.queue.size(), 1)
        self.queue.get()
        self.assertEquals(self.queue.size(), 0)
        self._fill()
        self.assertEquals(self.queue.size(), MAX_SIZE)

        # Manually clear it
        self.queue.queue = deque()
        self.assertEquals(self.queue.size(), 0)


    def test_clear(self):
        self.assertEquals(self.queue.size(), 0)
        self._fill(2)
        self.assertEquals(self.queue.size(), 2)
        result = self.queue.clear()
        self.assertEquals(result, 2)
        self.assertEquals(self.queue.size(), 0)

        # Clearing empty allowed
        result = self.queue.clear()
        self.assertEquals(result, 0)
        self.assertEquals(self.queue.size(), 0)

    def test_save(self):
        # Starts off right
        self.assertEquals(self.queue.size(), 0)
        # Empty save returns empty
        result = self.queue.save()
        self.assertIs(result, 0)
        self.assertEquals(self.queue.size(), 0)

        # Fill it up
        self._fill()
        self.assertEquals(self.queue.size(), MAX_SIZE)

        # Save clears the queue
        result = self.queue.save()
        self.assertIs(result, MAX_SIZE)
        self.assertEquals(self.queue.size(), 0)

        # TODO: Test it hits Db.

        # Back to normal behavior
        self.queue.append(self.sample)
        self.assertEquals(self.queue.size(), 1)

    def test_overflow(self):
        # Starts off right
        self.assertEquals(self.queue.size(), 0)
        # Fill it up
        self._fill()
        self.assertEquals(self.queue.size(), 3)
        # Overflow triggers save/clear
        self.queue.append(self.sample)
        self.assertEquals(self.queue.size(), 0)
        # Back to normal behavior
        self.queue.append(self.sample)
        self.assertEquals(self.queue.size(), 1)

    def test_defer(self):
        # Starts off right
        self.assertEquals(self.queue.size(), 0)
        self.queue.append(self.sample)
        self.assertEquals(self.queue.size(), 1)

        # Set up deferring
        self.queue.defer_save()
        self.assertIs(self.queue.save_deferred, True)
        # No change to queue
        self.assertEquals(self.queue.size(), 1)

        # Fill it up
        self._fill(MAX_SIZE)
        self.assertEquals(self.queue.size(), MAX_SIZE)

        # Overflow it
        self.queue.append(self.sample)
        self.assertEquals(self.queue.size(), 4)
        self.queue.append(self.sample)
        self.assertEquals(self.queue.size(), 5)
        # Turn deferring off, triggering save/clear
        self.queue.defer_save(False)
        self.assertEquals(self.queue.size(), 0)

        # Back to normal behavior
        self._fill()
        self.assertEquals(self.queue.size(), MAX_SIZE)
        self.queue.append(self.sample)
        self.assertEquals(self.queue.size(), 0)

        # Overflow a LOT
        self.queue.defer_save()
        self._fill(2000)
        self.assertEquals(self.queue.size(), 2000)
        self.queue.clear()

    def test_allow_save(self):
        # Starts off right
        self.assertEquals(self.queue.size(), 0)

        # Does nothing
        result = self.queue.allow_save()
        self.assertIs(result, 0)
        self.assertEquals(self.queue.size(), 0)

        # Set up deferring
        self.queue.defer_save()
        self.assertEquals(self.queue.size(), 0)

        # Fill it up
        self._fill( MAX_SIZE + 10 )
        self.assertEquals(self.queue.size(), MAX_SIZE + 10)

        # Permit saves again
        result = self.queue.allow_save()
        self.assertIs(result, MAX_SIZE + 10)
        self.assertEquals(self.queue.size(), 0)

        # We're still deferred
        self.assertIs(self.queue.save_deferred, True)
        self._fill(MAX_SIZE + 10)
        self.assertEquals(self.queue.size(), MAX_SIZE + 10)

    def test_defer_param(self):
        # Starts off right
        self.assertEquals(self.queue.size(), 0)

        # Does nothing special (yet)
        for i in range(MAX_SIZE):
            result = self.queue.append(self.sample, defer_save=True)
            self.assertEquals(result, i+1)
            self.assertEquals(self.queue.size(), i+1)
        self.assertEquals(self.queue.size(), MAX_SIZE)

        # Not set to defer all.
        self.assertIs(self.queue.save_deferred, False)

        # Param still defers
        result = self.queue.append(self.sample, defer_save=True)
        self.assertEquals(result, MAX_SIZE + 1)
        self.assertEquals(self.queue.size(), MAX_SIZE + 1)
        result = self.queue.append(self.sample, defer_save=True)
        self.assertEquals(result, MAX_SIZE + 2)
        self.assertEquals(self.queue.size(), MAX_SIZE + 2)

        # No param clears whole queue
        result = self.queue.append(self.sample, defer_save=False)
        self.assertEquals(result, 0)
        self.assertEquals(self.queue.size(), 0)

        # Back to normal
        for i in range(MAX_SIZE):
            self._append(i + 1)
        self.assertEquals(self.queue.size(), MAX_SIZE)
        self._append(0)

    def test_with(self):
        with self.queue as queue:
            # Starts normal
            self.assertEquals(queue.size(), 0)
            for i in range(queue.limit):
                result = queue.append(self.sample)
                self.assertIs(result, i + 1)
                self.assertIs(queue.size(), i + 1)
                # Interacting with self.queue as well
                self.assertIs(self.queue.size(), i + 1)
            self.assertIs(queue.size(), queue.limit)

            # Normal overflow
            queue.append(self.sample)
            self.assertIs(queue.size(), 0)
            self.assertIs(self.queue.size(), 0)

            # Fill it up
            queue.append(self.sample)
            queue.append(self.sample)
            self.assertIs(queue.size(), 2)

        # End the with loop, which calls save/clear
        self.assertIs(self.queue.size(), 0)
        # TODO: Check data is in DB.

        # Queue still works
        result = queue.append(self.sample)
        self.assertIs(result, 1)
        self.assertIs(self.queue.size(), 1)

    def test_init_required(self):
        with self.assertRaises(TypeError):
            Queue(limit=3)

        # No other params are required (and therefore don't throw exceptions)
        Queue(unique_key='rowid')

    """
    def test_force_save(self):
        raise NotImplementedError()

    def test_delete(self):
        raise NotImplementedError()

    def test_init(self):
        raise NotImplementedError()

    def test_multithreading(self):
        raise NotImplementedError()

    def test_multiple_queues(self):
        raise NotImplementedError()

    def test_model_type(self):
        raise NotImplementedError()

    def test_uniquekey(self):
        raise NotImplementedError()

    def test_define_args_in_class(self):
        raise NotImplementedError()

    def test_define_args_in_class_and_init(self):
        raise NotImplementedError()

    def test_enumerating(self):
        raise NotImplementedError()

    def test_bad_data(self):
        raise NotImplementedError()

    def test_internal_deque(self):
        raise NotImplementedError()

    def test_internal_queue(self):
        raise NotImplementedError()
    """
'''