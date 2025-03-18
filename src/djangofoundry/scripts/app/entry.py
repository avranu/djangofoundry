"""
Work in progress. App.py should be migrated to separate scripts, which are loaded dynamically. 

TODO App.py needs to be modified to use this.
"""
import argparse
import importlib

from djangofoundry.scripts.app.actions import Actions


class UnsupportedCommandError(Exception):
	"""
	Raised when an unsupported command is passed to the script.
	"""

def main():
	parser = argparse.ArgumentParser(description='Setup and manage the Django application.')
	parser.add_argument('action', choices=[e.value for e in Actions], help='The action to perform.')
	parser.add_argument('-p', '--project-name', default='myproject', help='The name of the project.')
	parser.add_argument('-a', '--author-name', help='The name of the author.')
	parser.add_argument('-d', '--directory', default='.', help='The directory for the project.')
	parser.add_argument('-f', '--frontend-dir', default='frontend', help='The directory for the frontend (relative to -d).')
	parser.add_argument('-b', '--backend-dir', default='backend', help='The directory for the backend (relative to -d).')
	parser.add_argument('-s', '--settings', default='conf/settings.yaml', help='The settings file to use.')
	args = parser.parse_args()

	try:
		# Dynamically import the appropriate script based on the action. For example, action "setup" should import setup.py in this dir.
		script = importlib.import_module(f'djangofoundry.scripts.app.{args.action}')
	except ModuleNotFoundError:
		raise UnsupportedCommandError(f'Unsupported command: {args.action}')

	# Call the main function of the script with the appropriate arguments
	script.main(args.project_name, args.author_name, args.settings, args.directory, args.frontend_dir, args.backend_dir)

if __name__ == '__main__':
	main()
