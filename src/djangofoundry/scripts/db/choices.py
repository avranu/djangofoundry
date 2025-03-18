from __future__ import annotations

from enum import Enum


class Actions(Enum):
	"""
	Defines the options we allow to be passed in from the command line when this script is run.

	Attribues:
		status:
			check the DB status
		start:
			start the DB (if it is not already running)
		restart:
			stop the DB (if it is running) and start it again.
		stop:
			stop the DB (if it is running)
	"""

	START = 'start'
	RESTART = 'restart'
	STATUS = 'status'
	STOP = 'stop'
	CHECK_ERRORS = 'check_errors'
	ANALYZE = 'analyze'
	REPAIR_ERRORS = 'repair_errors'
	MANAGE = 'manage'
	DEAD_ROWS = 'dead_rows'
	LONG_QUERIES = 'long_queries'
	LOCKS = 'locks'

	def __str__(self):
		"""
		Turns an option into a string representation
		"""
		return self.value
	

# pg_ctl exit codes
# https://www.postgresql.org/docs/current/app-pg-ctl.html
class PostgresStatusCodes:
    RUNNING = 0
    NOT_RUNNING = 3
    NO_DATA_DIR = 4

    @classmethod
    def running_codes(cls) -> list[int]:
        return [cls.RUNNING]
    
    @classmethod
    def not_running_codes(cls) -> list[int]:
        return [cls.NOT_RUNNING, cls.NO_DATA_DIR]
    
    @classmethod
    def error_codes(cls) -> list[int]:
        return [cls.NO_DATA_DIR]

    @classmethod
    def is_running(cls, status_code : int) -> bool:
        return status_code in cls.running_codes()
    
    @classmethod
    def is_stopped(cls, status_code : int) -> bool:
        return status_code in cls.not_running_codes()
    
    @classmethod
    def encountered_error(cls, status_code : int) -> bool:
        return status_code in cls.error_codes()
