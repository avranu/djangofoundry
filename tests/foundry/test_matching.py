"""

	Metadata:

		File: test_matching.py
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
from djangofoundry.matching.engine import MatchingEngine
from djangofoundry.matching.fuzzy import TheFuzz

class TheFuzzTestCase(TestCase):
	'''
	Tests the TheFuzz class
	'''

	def setUp(self):
		self.fuzz = TheFuzz()

	def test_find_best_match(self):
		input_str = "apple"
		choices = ["apple", "banana", "orange"]
		result = self.fuzz.choose(input_str, choices)
		self.assertEqual(result, ('apple', 100))

	def test_exact_match_ratio(self):
		input1 = "apple"
		input2 = "banana"
		result = self.fuzz.match(input1, input2)
		self.assertEqual(result, 18)

	def test_partial_match_ratio(self):
		input1 = "apple is good"
		input2 = "banana is bad"
		result = self.fuzz.partial_match(input1, input2)
		self.assertEqual(result, 48)

	def test_token_sort_match_ratio(self):
		input1 = "apple on sale"
		input2 = "on sale apple"
		result = self.fuzz.token_match(input1, input2)
		self.assertEqual(result, 100)

	def test_token_set_match_ratio(self):
		input1 = "apple on the tree"
		input2 = "tree apple"
		result = self.fuzz.token_partial_match(input1, input2)
		self.assertEqual(result, 100)

from tests.testcase import TestCase

class TestMatchingEngine(TestCase):
	'''
	Tests the MatchingEngine class
	'''
	def setUp(self):
		self.matching_engine: MatchingEngine = TheFuzz()

	def test_choose(self):
		input_str = "test"
		choices = ["test1", "test2", "test3"]
		required_confidence = 90
		result = self.matching_engine.choose(input_str, choices, required_confidence)
		self.assertIsInstance(result, tuple)
		self.assertIsInstance(result[0], str)
		self.assertIsInstance(result[1], int)

	def test_match(self):
		input_str = "hello"
		compare = "hello world"
		result = self.matching_engine.match(input_str, compare)
		self.assertIsInstance(result, int)

	def test_partial_match(self):
		input_str = "hello"
		compare = "hello world"
		result = self.matching_engine.partial_match(input_str, compare)
		self.assertIsInstance(result, int)

	def test_token_match(self):
		input_str = "hello"
		compare = "hello world"
		result = self.matching_engine.token_match(input_str, compare)
		self.assertIsInstance(result, int)

	def test_token_partial_match(self):
		input_str = "hello"
		compare = "hello world"
		result = self.matching_engine.token_partial_match(input_str, compare)
		self.assertIsInstance(result, int)