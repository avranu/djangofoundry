import logging
import pathlib
from typing import Callable

from djangofoundry.scripts.db.choices import Actions

logger = logging.getLogger(__name__)

def get_app_dir( directory : str ) -> pathlib.Path:
	"""
	Returns the path to the data or logs directory, depending on the directory option passed.
	
	Args:
		directory (str): The directory to return. Must be either "data" or "logs".

	Returns:
		dir_path (pathlib.Path): The path to the directory requested.

	Raises:
		ValueError: If the directory option passed is not valid.

	Examples:
		>>> get_app_dirs("data")
		PosixPath('/home/jess/postgres/data')
		>>> get_app_dirs("logs")
		PosixPath('/home/jess/postgres/logs')
		>>> get_app_dirs("invalid")
		Traceback (most recent call last):

	"""
	home_dir = pathlib.Path.home()

	match directory.lower():
		case 'data':
			dir_path = home_dir / "postgres" / "data"
		case 'logs':
			dir_path = home_dir / "postgres" / "logs"
		case _:
			raise ValueError(f'Invalid directory option: "{directory}". Use "data" or "logs" instead.')

	dir_path.mkdir(parents=True, exist_ok=True)
	
	return dir_path

# Define a decorator that allows us to register a class method to the actions dict
REGISTERED_ACTIONS : dict[str, Callable] = {}
def db_action(action_name : str|Actions) -> Callable:
	"""
	Decorator that registers a class method to the actions dict. 
	
	This isn't called directly. Use it prior to a class method definition like so:
	@db_action('status')
	"""
	def decorator(func : Callable) -> Callable:
		if isinstance(action_name, Actions):
			idx = str(action_name)
		else:
			idx = action_name
		
		logger.debug(f'Registering action: {idx} to {func}')
		REGISTERED_ACTIONS[idx] = func

		return func
	
	return decorator
