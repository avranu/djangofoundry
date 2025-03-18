"""

Metadata:

File: settings.py
Project: Django Foundry
Created Date: 16 Sep 2022
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

import logging
import logging.config
import os
from typing import Any

import yaml
from yaml.loader import SafeLoader

# App imports
from djangofoundry.scripts.utils.exceptions import FileEmptyError
from djangofoundry.scripts.utils.types import SettingsFile, SettingsLog

DEFAULT_SETTINGS_PATH : str = '../conf/sample-settings.yaml'

class Settings:
	"""
	Settings for our application (used in /bin files only).

	These are loaded from the file at SETTINGS_PATH (currently bin/conf/settings.yaml).
	"""

	_settings : SettingsFile | None = None
	_logging_setup : bool = False

	def __init__(self, settings_path : str = DEFAULT_SETTINGS_PATH):
		# Check if the settings file exists
		if not os.path.exists(settings_path):
			# Load the default config, which is relative to this file's path
			settings_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), DEFAULT_SETTINGS_PATH)

		# Load our settings
		self.load_config(settings_path)

		# If we still don't have any settings, then raise an error
		if not self._settings:
			raise FileEmptyError(f'No settings found in {settings_path}')

	@property
	def settings(self) -> SettingsFile:
		# If settings has never been loaded, then load it.
		if not self._settings:
			self.load_config()

			if not self._settings:
				raise FileEmptyError(f'No settings found in {DEFAULT_SETTINGS_PATH}')

		# It should exist now
		return self._settings


	@property
	def logging(self) -> SettingsLog:
		return self.settings.get('logging')


	def getLogger(self, namespace : str):
		"""
		Sets up the logger once (and only once), then returns a logger for the module requested.
		"""
		# Setup logging if it isn't already
		if self._logging_setup is not True:
			try:
				logging.config.dictConfig(Settings.logging.__dict__)
			except Exception as e:
				print(f'Unable to set up logging: {e}')
				raise e from e
			self._logging_setup = True

		# Create a new logger
		return logging.getLogger(namespace)


	def load_config(self, settings_path : str = DEFAULT_SETTINGS_PATH) -> SettingsFile:
		# Read our default sensitivity settings (if available)
		filepath = os.path.join(os.path.dirname(os.path.abspath(__file__)), settings_path)

		if os.path.exists(filepath):
			# If it exists, then open it
			with open(filepath, encoding='utf-8') as file:
				# Load the contents into a variable
				self._settings = yaml.load(file, Loader=SafeLoader)
		else:
			# Let everyone know we couldn't find the settings. This likely exits.
			raise FileNotFoundError(f"Could not load bin settings from {filepath}")

		# Validate contents of settings file.
		if self._settings == {}:
			raise FileEmptyError(f'No data in settings file at f{filepath}')

		return self._settings


	def all(self) -> SettingsFile:
		"""
		Makes the syntax for getting the settings dict a little less clunky (i.e. Settings.all() instead of Settings.settings)

		Returns:
			dict: A dictionary of settings.

		"""
		return self.settings


	def get(self, key : str) -> Any:
		"""
		Retrieves the value at the provided key.

		Args:
			key (str): A key to retrieve

		Returns:
			Any: The value stored at the provided key

		"""
		return self.settings.get(key)

if __name__ == '__main__':
	conf = Settings.settings
	print(conf)
