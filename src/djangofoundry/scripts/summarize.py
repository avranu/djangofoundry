import argparse
import ast
import logging
import os
from typing import Any, Union

# Configure logger to print to output
logging.basicConfig(level=logging.DEBUG, handlers=[logging.StreamHandler()])
logger = logging.getLogger(__name__)

class PythonClassParser:
	"""
	Parser for Python classes in a directory.

	This class will parse all Python files in a directory and output a summary of all classes found in those files, which can be used
	to generate documentation for the project, or to pass to other tools (like LLMs).
	"""

	def __init__(self, directory: str, output_file: str, ignored_paths: list[str], recursive: bool) -> None:
		logger.debug(f"Initializing PythonClassParser: {directory} : {output_file}")
		self.directory: str = directory
		self.output_file: str = output_file
		self.printed_module_names: set[str] = set()
		self.ignored_paths: list[str] = ignored_paths
		self.recursive: bool = recursive

	@classmethod
	def is_ignored(cls, path: str, ignored_paths: list[str]) -> bool:
		for ignored in ignored_paths:
			if ignored in path:
				return True
		return False

	def find_python_files(self, directory: str) -> list[str]:
		"""
		Recursively find all Python files in a directory.
		"""
		python_files: list[str] = []
		try:
			for root, dirs, files in os.walk(directory):
				if not self.recursive:
					dirs[:] = []  # remove subdirectories from search
				for file in files:
					if file != '__init__.py' and file.endswith('.py'):
						file_path = os.path.join(root, file)
						if not self.is_ignored(file_path, self.ignored_paths):
							python_files.append(file_path)
		except OSError as e:
			logger.error(f"Failed to walk directory {directory}: {e}")
		return python_files

	@classmethod
	def parse_file(cls, file: str) -> Union[ast.Module, None]:
		"""
		Parse a Python file and return the AST.
		"""
		try:
			with open(file, "r") as source:
				return ast.parse(source.read())
		except OSError as e:
			logger.error(f"Failed to open {file}: {e}")
			return None
		except SyntaxError as e:
			logger.error(f"Failed to parse {file}: {e}")
			return None

	@classmethod
	def get_return_type(cls, node: ast.FunctionDef) -> str:
		"""
		Get the return type of a function.
		"""
		try:
			if isinstance(node.returns, ast.Name):
				result = node.returns.id
			elif isinstance(node.returns, ast.Subscript):
				result = ast.unparse(node.returns).strip()
			elif isinstance(node.returns, ast.Attribute):
				result = ast.unparse(node.returns).strip()
			else:
				result = 'None'

			return cls.shorten_return_type(result)
		except TypeError as e:
			logger.error(f"Failed to get return type for {node.name}: {e}")
			return 'None'


	@classmethod
	def shorten_return_type(cls, return_type: str) -> str:
		"""
		Shorten a return type to a more readable format (and one which uses fewer tokens, when passed to an LLM)
		"""
		# Turn 'Union[None, str]' into 'str'
		if return_type.startswith('Union[None'):
			return_type = return_type[return_type.rfind(',') + 2:-1]

		# Turn 'Optional[str]' into 'str'
		if return_type.startswith('Optional['):
			return_type = return_type[return_type.rfind('[') + 1:-1]

		# Turn list[str] into str[]
		if return_type.startswith('list['):
			return_type = return_type.replace('list[', '')[:-1] + '[]'

		# Turn dict[str, int] into {int}
		if return_type.startswith('dict['):
			return_type = return_type.replace('dict[', '{')[:-1] + '}'

		# Turn Tuple[str, int] into (str, int)
		if return_type.startswith('Tuple['):
			return_type = return_type.replace('Tuple[', '(')[:-1] + ')'

		# Turn Union[str, int] into str|int
		if return_type.startswith('Union['):
			return_type = return_type.replace('Union[', '').replace(',', '|')[1:-1]

		# Turn Iterable[str] into str[]
		if return_type.startswith('Iterable['):
			return_type = return_type.replace('Iterable[', '')[:-1] + '[]'

		# Turn Any[] into []
		if return_type == 'Any[]':
			return_type = '[]'

		return return_type

	@classmethod
	def get_method_signature(cls, node: ast.FunctionDef) -> str:
		"""
		Get the signature of a method.
		"""
		try:
			args = [param.arg for param in node.args.args if param.arg not in ['self', 'cls']]

			method = f"{node.name}({', '.join(args)})"
			return_type = cls.get_return_type(node)
			if return_type == 'None':
				return method
			return f"{method} {cls.get_return_type(node)}"
		except Exception as e:
			logger.error(f"Failed to get method signature for {node.name}: {e}")
			return ''

	@classmethod
	def find_classes_and_methods(cls, tree: ast.Module) -> dict[str, dict[str, Any]]:
		"""
		Find all classes and methods in a Python file.
		"""
		classes: dict[str, dict[str, Any]] = {}
		for node in ast.walk(tree):
			if isinstance(node, ast.ClassDef):
				class_name: str = node.name
				base_classes: list[str] = [base.id for base in node.bases if isinstance(base, ast.Name)]
				method_names: list[str] = [cls.get_method_signature(n) for n in node.body if isinstance(n, ast.FunctionDef) and not n.name.startswith('_')]
				if method_names:  # Ignore classes with no methods (other than __init__)
					classes[class_name] = {"name": class_name, "base_classes": base_classes, "methods": method_names}
		return classes

	@classmethod
	def group_classes_by_module(cls, classes: dict[str, list[dict[str, Any]]], module_name: str) -> list[dict[str, Any]]:
		"""
		Group classes by module name.
		"""
		if module_name not in classes:
			classes[module_name] = []
		return classes[module_name]

	def write_to_file(self, grouped_classes: dict[str, list[dict[str, Any]]]) -> None:
		"""
		Write classes and methods to a file.
		"""
		with open(self.output_file, 'a') as f:
			for module_name, classes in grouped_classes.items():
				if not classes:  # Skip empty modules
					continue

				f.write(f"#{module_name}\n")

				for class_data in classes:
					try:
						base_classes_str = '(' + ', '.join(class_data['base_classes']) + ')' if class_data['base_classes'] else ''
						f.write(f"{class_data['name']}{base_classes_str}\n")
						for method in class_data['methods']:
							f.write(f"\t{method}\n")

						logger.debug(f"Wrote {class_data['name']} and {len(class_data['methods'])} methods to {self.output_file}")
					except KeyError as e:
						logger.error(f"Failed to write {class_data}: {e}")

				f.write("\n")

	def run(self) -> None:
		"""
		Run the summarizer.
		"""
		# Clear output file
		if os.path.exists(self.output_file):
			os.remove(self.output_file)

		# Write header text to output file
		with open(self.output_file, 'a') as f:
			f.write("Summarized as:\n#Directory\nClass\n\tmethods\n\nOmitted self/cls params, methods beginning with _\n\n--\n\n")

		grouped_classes: dict[str, list[dict[str, Any]]] = {}
		for file in self.find_python_files(self.directory):
			tree = self.parse_file(file)
			if tree is not None:
				logger.debug(f"Parsing {file}")
				module_classes = self.find_classes_and_methods(tree)
				relative_path = os.path.relpath(file, self.directory)
				module_name = os.path.dirname(relative_path).replace(os.path.sep, '.')
				self.group_classes_by_module(grouped_classes, module_name).extend(module_classes.values())
			else:
				logger.warning(f"Failed to parse {file}")
		self.write_to_file(grouped_classes)
		logger.info(f"Finished parsing {self.directory}")

def parse_args() -> argparse.Namespace:
	"""
	Parse command line arguments.
	"""
	parser = argparse.ArgumentParser(description="Find all classes and their methods in Python files in a directory.")
	parser.add_argument('-d', '--directory', type=str, default='.', help="Directory to search for Python files")
	parser.add_argument('-o', '--output', type=str, default='project_summary.txt', help="Output file")
	parser.add_argument('-i', '--ignore', nargs='*', default=[], help="Directories or files to ignore")
	parser.add_argument('-l', '--logfile', type=str, help="Log file")
	parser.add_argument('-r', '--recursive', action='store_true', help="Enable or disable recursive search in subdirectories", default=True)
	parser.add_argument('-v', '--verbose', action='store_true', help="Print debug messages")
	return parser.parse_args()

if __name__ == "__main__":
	args : argparse.Namespace = parse_args()
	if args.verbose:
		logger.setLevel(logging.DEBUG)

	if args.logfile:
		file_handler = logging.FileHandler(args.logfile)
		logger.addHandler(file_handler)

	arg_parser : PythonClassParser = PythonClassParser(args.directory, args.output, args.ignore, args.recursive)
	arg_parser.run()
