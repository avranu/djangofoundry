"""
*****************************************************************************
*                                                                             *
* Metadata:                                                                   *
*                                                                             *
* 	File: db.py                                                                *
* 	Project: django-foundry                                                    *
* 	Created: 08 Jun 2023                                                       *
* 	Author: Jess Mann                                                          *
* 	Email: jess.a.mann@gmail.com                                               *
*                                                                             *
* 	-----                                                                      *
*                                                                             *
* 	Last Modified: Mon Oct 02 2023                                             *
* 	Modified By: Jess Mann                                                     *
*                                                                             *
* 	-----                                                                      *
*                                                                             *
* 	Copyright (c) 2023 Jess Mann                                               *
****************************************************************************
"""
#!/usr/bin/env python

# Generic imports
import argparse
import logging
import os
import pathlib
import re
import shutil
import subprocess
import sys
import textwrap
import time
from shutil import which

# Our imports
from djangofoundry.scripts.db.choices import Actions, PostgresStatusCodes
from djangofoundry.scripts.db.constants import DEFAULT_DATA_PATH, DEFAULT_LOG_PATH, EXE
from djangofoundry.scripts.db.functions import REGISTERED_ACTIONS, db_action
from djangofoundry.scripts.utils.action import EnumAction

# Set up logging
logger = logging.getLogger(__name__)

class Db:
	"""
	Manages a database instance. This class is responsible for starting, stopping, and restarting the database.

	Attributes:
		data_path (str):
			The path to the data directory for the database.
		log_path (str):
			The path to the logfile for the database.
		user (str):
			The user to run the database as.
		database (str):
			The name of the database to use.

	"""

	_data_path : str
	_log_path : str
	_user : str
	_database : str

	@property
	def log_path(self) -> str:
		return self._log_path

	@property
	def data_path(self) -> str:
		return self._data_path

	@property
	def user(self) -> str:
		return self._user

	@property
	def database(self) -> str:
		return self._database

	@log_path.setter
	def log_path(self, user_input_path : str|pathlib.Path) -> None:
		"""
		Sets the log path. Assumes that input_path is user input and sanitizes it accordingly.

		Args:
			user_input_path (str): The path provided via user input to sanitize and set.

		Returns:
			None

		"""
		self._log_path = self.sanitize_path(user_input_path)

	@data_path.setter
	def data_path(self, user_input_path : str|pathlib.Path) -> None:
		"""
		Sets the data directory path. Assumes that input_path is user input and sanitizes it accordingly.

		Args:
			user_input_path(str): The path provided via user input to sanitize and set.

		Returns:
			None

		"""
		self._data_path = self.sanitize_path(user_input_path)

	def __init__(self, data_path: str|pathlib.Path = DEFAULT_DATA_PATH, log_path: str|pathlib.Path = DEFAULT_LOG_PATH):
		"""
		Sets up our Db object with config options we'll use for this run.

		Args:
			data_path(str, optional)
				The data directory path to use, which is passed directly to Postgres.
				Note: This is sanitized and only accepts these characters: a-zA-Z0-9/_.-
				On windows, this also accepts colons and backslashes.
				Defaults to the DEFAULT_DATA_PATH constant.
			log_path
				The logfile we want Postgres to use.
				Note: This is sanitized and only accepts these characters: a-zA-Z0-9/_.-
				On windows, this also accepts colons and backslashes.
				Defaults to the DEFAULT_LOG_PATH constant.

		Raises:
			ValueError: If the config options provided are not valid, or the files they reference are not found.
			FileNotFoundError: If the postgres executable cannot be found.

		"""
		# Validation
		if not os.path.isdir(data_path):
			raise ValueError(f'Data path not found: "{data_path}"')
		if not os.path.isfile(log_path):
			raise ValueError(f'Log path not found: "{log_path}"')
		if which(EXE) is None:
			raise FileNotFoundError(f'DB executable not found. Is "{EXE}" in your path?')

		# Set our paths. Note: This calls the property setter, which sanitizes them.
		self.data_path = data_path
		self.log_path = log_path

		self._user = os.environ.get('django_foundry_db_user', 'postgres')
		self._database = os.environ.get('django_foundry_db_database', 'DjangoFoundry')

	def create_data_dir(self) -> None:
		"""
		Creates the data directory if it does not exist.

		Returns:
			None

		"""
		if not os.path.isdir(self.data_path):
			os.makedirs(self.data_path)

	def move_data_dir(self, new_path: str|pathlib.Path) -> bool:
		"""
		Moves the data directory to a new location.

		Args:
			new_path(str): The new path to move the data directory to.

		Returns:
			bool: True if the directory now exists at the new path, False otherwise.

			NOTE: This will return True if the directory already exists at the new path, so was not moved.

		Raises:
			ValueError: If the new path is not valid.

		"""
		# Validate the new path
		new_path = self.sanitize_path(new_path)

		# If it's the same as our current path, then we're done.
		if new_path == self.data_path:
			logger.info("Data directory already at '%s'. Skipping move.", new_path)
			return True

		# If it's not the same, then we need to move the directory.
		shutil.move(self.data_path, new_path)
		self.data_path = new_path

		# Make sure the directory exists at the new path.
		return os.path.isdir(self.data_path)

	@db_action(Actions.START)
	def start(self) -> bool:
		"""
		Starts the PostgresSQL server (if it is not running) and prints all output to stdout.

		If the server is already running, prints a message indicating so, but does NOT attempt to restart.

		Returns:
			bool: True if the server is running now (regardless of whether we had to start it), False otherwise. 

		"""
		# If we're already running, then just return right away.
		if self.is_running():
			logger.info("Postgres server already running")
			return True

		# Okay, not running. Try starting it with subprocess.run
		result = subprocess.run([EXE, '-D', self.data_path, '-l', self.log_path, 'start'], check=False).returncode

		# If the result is 0, then we started successfully.
		if result == 0:
			logger.info("Postgres server started successfully")
			return True
		
		# Otherwise, we failed to start.
		logger.error("Postgres server failed to start")
		return False

	@db_action(Actions.RESTART)
	def restart(self) -> bool:
		"""
		Restarts the PostgresSQL server and prints all output to stdout.

		Returns:
			bool: True if the server is running now (regardless of whether we had to start it), False otherwise.

		"""
		result = subprocess.run([EXE, '-D', self.data_path, '-l', self.log_path, 'restart'], check=True).returncode

		# If the result is 0, then we started successfully.
		if result == 0:
			logger.info("Postgres server restarted successfully")
			return True
		
		# Otherwise, we failed to start.
		logger.error("Postgres server failed to restart")
		return False

	@db_action(Actions.STOP)
	def stop(self) -> bool:
		"""
		Stops the PostgresSQL server and prints all output to stdout.

		Returns:
			bool: True if the server is stopped now (regardless of whether we had to stop it), False if it is still running.

		"""
		try:
			result = subprocess.run([EXE, '-D', self.data_path, '-l', self.log_path, 'stop'], check=True).returncode
		except subprocess.CalledProcessError as e:
			# If the return code is 3, then the server was not running, so we can just return True.
			if e.returncode == 3:
				logger.info("Postgres server already stopped")
				return True

			# Otherwise, we failed to stop it.
			logger.error("Postgres server failed to stop")
			return False

		# If the result is 0, then we stopped it successfully
		if result == 0:
			logger.info("Postgres server stopped successfully")
			return True
		
		# Otherwise, we failed to stop it.
		logger.error("Postgres server failed to stop")
		return False

	@db_action(Actions.STATUS)
	def status(self) -> bool:
		"""
		Checks the status of the postgres server and prints all output to stdout.

		Returns:
			bool: True if it is running, False otherwise. 

		"""
		result = subprocess.run([EXE, '-D', self.data_path, '-l', self.log_path, 'status'], check=False).returncode

		if PostgresStatusCodes.encountered_error(result):
			logger.warning('Encountered error while checking status. Postgres error code %s', result)

		if PostgresStatusCodes.is_running(result):
			return True
		
		return False

	@db_action(Actions.CHECK_ERRORS)
	def check_errors(self) -> bool:
		"""
		Checks the postgres server for errors and prints all output to stdout.

		Returns:
			bool: True if there are no errors (i.e. success), False if we detect errrors (i.e. failure).

		"""
		cmd = ['psql', '-U', self.user, '-d', self.database, '-c', "SELECT * FROM pg_stat_database_conflicts WHERE datname = current_database();"]
		result = subprocess.call(cmd)

		if result == 0:
			logger.info("No errors detected")
			return True
		
		logger.error("Errors detected")
		return False

	@db_action(Actions.ANALYZE)
	def analyze(self) -> int:
		"""
		Runs an ANALYZE VERBOSE on the database.
		"""
		cmd = ['psql', '-U', self.user, '-d', self.database, '-c', "ANALYZE VERBOSE;"]
		return subprocess.call(cmd)

	@db_action(Actions.REPAIR_ERRORS)
	def repair_errors(self) -> int:
		"""
		Runs a REINDEX DATABASE on the database.
		"""
		cmd = ['psql', '-U', self.user, '-d', self.database, '-c', "REINDEX DATABASE current_database;"]
		return subprocess.call(cmd)

	@db_action(Actions.DEAD_ROWS)
	def dead_rows(self) -> int:
		"""
		Checks for dead rows in the database.
		"""
		cmd = ['psql', '-U', self.user, '-d', self.database, '-c', "SELECT relname, n_dead_tup FROM pg_stat_user_tables WHERE n_dead_tup > 0;"]
		return subprocess.call(cmd)

	@db_action(Actions.LONG_QUERIES)
	def long_queries(self) -> int:
		"""
		Checks for long running queries in the database.
		"""
		cmd = ['psql', '-U', self.user, '-d', self.database, '-c', "SELECT pid, now() - pg_stat_activity.query_start AS duration, query FROM pg_stat_activity WHERE (now() - pg_stat_activity.query_start) > interval '5 minutes';"]
		return subprocess.call(cmd)

	@db_action(Actions.LOCKS)
	def locks(self) -> int:
		"""
		Checks for locks in the database.
		"""
		cmd = ['psql', '-U', self.user, '-d', self.database, '-c', "SELECT pid, relation::regclass, mode, granted FROM pg_locks WHERE NOT granted;"]
		return subprocess.call(cmd)

	@db_action(Actions.MANAGE)
	def manage(self) -> None:
		"""
		Manages the postgres server, restarting it if it is not running.
		"""
		while True:
			if not self.is_running():
				print("Postgres is not running. Starting it up...")
				self.start()
			else:
				print("Postgres is running.")
			time.sleep(5)

	def is_running(self) -> bool:
		"""
		Determines if the postgres server is running, without printing anything to stdout.

		Returns:
			bool: True if the server is running, False otherwise.

		Raises:
			FileNotFoundError: If postgres is not able to find the data directory

		"""
		# Create a child process, supressing output
		child = subprocess.run([EXE, '-D', self.data_path, 'status'], stdout = subprocess.PIPE)

		"""
		Postgres returns exit code 3 if the server is NOT running, and 4 on error. It returns 0 otherwise.

		See here: https://www.postgresql.org/docs/current/app-pg-ctl.html
			status mode checks whether a server is running in the specified data directory. If it is,
			the server's PID and the command line options that were used to invoke it are displayed.
			If the server is not running, pg_ctl returns an exit status of 3.
			If an accessible data directory is not specified, pg_ctl returns an exit status of 4.
		"""
		if child.returncode == 4:
			raise FileNotFoundError(f'Postgres is not able to find the data directory: {self.data_path}')
		return not child.returncode

	def sanitize_path(self, user_input_path : str|pathlib.Path) -> str:
		"""
		Takes arbitrary user input, and sanitizes it to prevent injection attacks.

		NOTE: The return value from this function will generally be passed directly to the command line,
		so we must be especially careful with what we return.

		Args:
			user_input_path (str|pathlib.Path): The user input to turn into a path

		Returns:
			str: The sanitized path

		"""
		# Convert to a string if it is a pathlib.Path
		if isinstance(user_input_path, pathlib.Path):
			user_input_path = str(user_input_path)

		# Whitelist "good" characters and remove all others
		if os.name == 'nt':
			# If we're running on windows, we must accept colons and backslashes
			return re.sub(r'[^a-zA-Z0-9:/\\_.-]', '', user_input_path)

		# If we're running on a sane operating system, don't allow colons or backslashes.
		return re.sub(r'[^a-zA-Z0-9/_.-]', '', user_input_path)
	
	def run(self, action : str|Actions) -> int:
		"""
		Runs the specified action.

		NOTE: This makes use of the REGISTERED_ACTIONS dict, which is populated using the @db_action decorator.
		
		Args:
			action (Actions): The action to run
		
		Returns:
			int: The exit code of the action

		"""
		# Convert the action to an string
		if isinstance(action, Actions):
			action = action.value

		# Check if the action is valid
		if action not in REGISTERED_ACTIONS:
			raise ValueError(f'Invalid action: {action}')

		# Run the action
		return REGISTERED_ACTIONS[action](self)

def main() -> None:
	"""
	Entry point for the script
	"""
	# Setup the basic configuration for the parser
	parser = argparse.ArgumentParser(
			formatter_class=argparse.RawTextHelpFormatter,
			description=textwrap.dedent("""
				Interact with the application's local DB
			"""),
			epilog="",
	)

	# Define the arguments we will accept from the command line.
	# allow case insensitive actions
	parser.add_argument('action',
					type=Actions,
					action=EnumAction,
					help=textwrap.dedent("""\
						Start the local application DB

						status: check the DB status
						start: start the DB (if it is not already running)
						restart: stop the DB (if it is running) and start it again.
						stop: stop the DB (if it is running)
						check_errors: check for errors in the DB
						repair_errors: repair errors in the DB
						analyze: analyze the DB
						dead_rows: check for dead rows in the DB
						long_queries: check for long running queries in the DB
						locks: check for locks in the DB
						manage: manage the DB, restarting it if it is not running
					"""))
	parser.add_argument('-a', '--app',
					type=str,
					metavar='app',
					default='djangofoundry',
					help="Name of the application.")
	parser.add_argument('-l', '--log',
						type=str,
						metavar='path',
						default=DEFAULT_LOG_PATH,
						help="Path to the log file for the DB.")
	parser.add_argument('-d', '--data',
						type=str,
						metavar='path',
						default=DEFAULT_DATA_PATH,
						help="Path to the data directory for postgres.")
	parser.add_argument('--level', '-v',
						type=str,
						metavar='level',
						default='info',
						choices=['debug', 'info', 'warning', 'error', 'critical'],
						help="The log level to use.")

	# Parse the arguments provided to our script from the command line
	# These are used as attributes. For example: options.action
	options = parser.parse_args()

	# Set the logger config as basic, output to console
	logging.basicConfig(
		level=options.level.upper(),
		format='%(asctime)s %(levelname)s %(message)s',
		datefmt='%Y-%m-%d %H:%M:%S',
		handlers=[logging.StreamHandler()],
		stream=sys.stdout
	)

	try:
		# Instantiate a new DB object based on our arguments
		db = Db(data_path=options.data, log_path=options.log)
	except ValueError as ve:
		# One of the options contains bad data. Print the message and exit.
		print(f'Bad option provided: {ve}')
		sys.exit()
	except FileNotFoundError as fnf:
		# The options were okay, but we can't find a necessary file (probably the executable)
		print(f'Unable to find a necessary file: {fnf}')
		sys.exit()

	result = db.run(options.action)

	sys.exit(result)

if __name__ == '__main__':
	"""
		This code is only run when this script is called directly (i.e. python bin/db.py)
	"""
	main()
