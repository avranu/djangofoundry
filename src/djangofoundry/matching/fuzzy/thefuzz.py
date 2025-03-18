"""

Metadata:

File: thefuzz.py
Project: Django Foundry
Created Date: 26 Mar 2023
Author: Jess Mann
Email: jess.a.mann@gmail.com

-----

Last Modified: Wed May 10 2023
Modified By: Jess Mann

-----

Copyright (c) 2023 Jess Mann
"""

from __future__ import annotations

from typing import Iterable

from thefuzz import fuzz, process

from djangofoundry.matching.engine import MatchingEngine


class TheFuzz(MatchingEngine):
	"""
	A matching engine that uses thefuzz library to match strings
	"""

	def choose( self, input_str : str, choices : Iterable[str], required_confidence : int = 90 ) -> tuple[str | None, int]:
		"""
		Use the matching engine to pick the best option from a group of options

		Args:
			input_str (str):
				The input_str to attempt to match
			choices (Iterable[str]):
				A group of choices to pick between
			required_confidence (int, optional):
				The lowest confidence to "accept". If no match is found with this confidence, we will return None.
				Defaults to 90.

		Returns:
			tuple[str | None, int]:
			(match, confidence)

			Match: The matching choice, or None
			Confidence: The confidence of the match, from 1-100

		"""
		results = process.extractOne(str(input_str), choices, score_cutoff=required_confidence)

		if results is None:
			return (None, 0)

		# Check if there are 2 or 3 values in the tuple, and unpack
		if len(results) == 2:
			(matching_key, confidence) = results
		else:
			(matching_key, confidence, _index) = results

		# Sufficient match!
		return (matching_key, confidence)

	def match( self, input_str : str, compare : str ) -> int:
		"""
		Use the matching engine to determine the confidence that these two strings match.

		For example:
			"John Smith" == "John Smith"
			"John Edward Smith" != "John Smith"
			"Smith, John" != "John Smith"

		Args:
			input_str (str):
				The input_str to attempt to match
			compare (str):
				The string to compare against

		Returns:
			int:
				The confidence that these two strings match.
				1 - 100

				100 means we are certain they match.
				1 means we are certain they do not match.

		"""
		return fuzz.ratio(input_str, compare)

	def partial_match( self, input_str : str, compare : str ) -> int:
		"""
		Use the matching engine to determine the confidence that these two strings have a partial match.

		For example:
			"John Edward Smith" == "John Smith"

		Args:
			input_str (str):
				The input_str to attempt to match
			compare (str):
				The string to compare against

		Returns:
			int:
				The confidence that these two strings match.
				1 - 100

				100 means we are certain they match.
				1 means we are certain they do not match.

		"""
		return fuzz.partial_ratio(input_str, compare)

	def token_match( self, input_str : str, compare : str ) -> int:
		"""
		Use the matching engine to determine the confidence that each token (i.e. string part) of these two strings match.

		For example:
			"Smith, John" == "John Smith"

		Args:
			input_str (str):
				The input_str to attempt to match
			compare (str):
				The string to compare against

		Returns:
			int:
				The confidence that these two strings match.
				1 - 100

				100 means we are certain they match.
				1 means we are certain they do not match.

		"""
		return fuzz.token_sort_ratio(input_str, compare)

	def token_partial_match( self, input_str : str, compare : str ) -> int:
		"""
		Use the matching engine to determine the confidence that these two strings match.

		For example:
			"Smith, John Edward" == "John Smith"

		Args:
			input_str (str):
				The input_str to attempt to match
			compare (str):
				The string to compare against

		Returns:
			int:
				The confidence that these two strings match.
				1 - 100

				100 means we are certain they match.
				1 means we are certain they do not match.

		"""
		return fuzz.token_set_ratio(input_str, compare)
