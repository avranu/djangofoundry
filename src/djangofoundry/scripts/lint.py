"""

Metadata:

File: lint.py
Project: Django Foundry
Created Date: 18 Apr 2023
Author: Jess Mann
Email: jess.a.mann@gmail.com

-----

Last Modified: Fri Apr 28 2023
Modified By: Jess Mann

-----

Copyright (c) 2023 Jess Mann
"""
from __future__ import annotations

import argparse
import glob
import os
import re

import openai
import yaml
from tqdm import tqdm


class ChatGPTBugFixer:
	def __init__(self, api_key, args):
		openai.api_key = api_key
		self.args = args
		self.project_path = args.path
		self.max_chars = 10000

	def strip_comments(self, code : str) -> str:
		# Strip comments beginning with a hash
		code = re.sub(r"(?m)^\s*#.*\n?", "", code)

		# Strip comments beginning with a triple quote
		code = re.sub(r'(?s)""".*?"""', '', code)

		# Strip comments beginning with a single quote
		code = re.sub(r"(?s)'''.*?'''", '', code)

		# Strip module declarations, like __author__
		code = re.sub(r"(?m)^__.*__\s*=\s*.*\n?", "", code)

		return code

	def strip_standard_imports(self, code : str) -> str:
		# Strip standard library imports
		code = re.sub(r"(?m)^\s*import.*\n?", "", code)
		code = re.sub(r"(?m)^\s*from.*\n?", "", code)

		return code

	def strip_common_code(self, code : str) -> str:
		# Remove logger = logging.getLogger(__name__)
		code = re.sub(r"(?m)^\s*logger = logging.getLogger\(__name__\)\s*\n?", "", code)
		return code

	def lint_code(self, code : str) -> str:
		# Run the code through a linter with autofixes
		return code

	def remove_blanks(self, code : str) -> str:
		# Remove blank lines
		code = re.sub(r"(?m)^\s*\n?", "", code)

		# Remove trailing spaces on a line
		code = re.sub(r"(?m)\s+$", "", code)

		return code

	def trim_code(self, code : str) -> str:
		code = self.strip_comments(code)
		code = self.strip_standard_imports(code)
		code = self.strip_common_code(code)
		code = self.lint_code(code)

		return code

	def submit_code_to_chatgpt(self, code, file_path) -> str:
		try:
			response = openai.ChatCompletion.create(
				model = "gpt-4",
				messages = [
					{"role": "system", "content": "Your job is to identify bugs in python code and suggest improvements, adhering to modern best " +
												  "practices, such as DRY. Review the code supplied and list specific changes to the code. If " +
												  "functionality can be added to the code, suggest them. Use the following format for your " +
												  "suggestions: 'Change Y to Z'. If there are no changes needed, respond with 'no changes proposed'. " +
												  "Example response format: In the `calculate` method, change 'area = length * length' to 'area = " +
												  "length * width'. All code submitted will be from a large django project using python 3.10 or higher, which " +
												  "is focused on data analytics and running background automation tasks. The code snippet provided " +
												  "is not the full file; it excludes all imports and comments in the original. When you are finished, " +
												  "adding as much functionality as you can and identifying bugs, please write django unit tests for " +
												  "the code for 100% code coverage"},
					{"role": "user", "content": f"File: `{file_path}`, Code: \n\n{code}"},
				]
			)
			# print the full response
			print(response)

			# Convert it to a format that we can subscript
			response = response.__dict__

			return f'''
			Tokens: {response['usage']}
			Model: {response['model']}
			Cost: ${response['usage']['total_tokens'] * 0.03 / 1000}
			Suggestions: \n{response['choices'][0]['message']['content']}
			'''
		except Exception as e:
			print(f"Error when submitting code to ChatGPT: {e}")
			return 'Error Retrieving Response. Please try again.'

	def process_python_files(self):
		python_files = glob.glob(f"{self.project_path}/**/*.py", recursive=True)

		# Exclude __init__.py, and other files that we don't want to check
		exclude = ["__init__.py", "settings.py", "urls.py", "wsgi.py", "asgi.py", "manage.py"]
		python_files = [file for file in python_files if os.path.basename(file) not in exclude]
		excluded_dirs = ['migrations', 'logs', 'tests', 'conf', 'settings', 'static', 'templates',
						 'node_modules', 'venv', 'build', 'dist', 'public', 'docs']
		for excluded_dir in excluded_dirs:
			python_files = [file for file in python_files if excluded_dir not in file]
		count = 0

		for file_path in tqdm(python_files, desc="Processing files", unit="file"):
			# Check if we've reached the max number of files to process
			if self.args.max > 0 and count > self.args.max:
				break

			diff_file_path = file_path + ".diff"
			if os.path.exists(diff_file_path):
				print(f"\nSkipping {file_path} as it already has a diff file.")
				continue

			try:
				with open(file_path, "r", encoding="utf-8") as source_code:
					code = source_code.read()
					code_no_comments = self.trim_code(code)

					# Exclude files that are too short
					if len(code_no_comments) < 300:
						print(f"\nSkipping {file_path} as it is too short.")
						continue

					# For now, exclude files that are too long
					if len(code_no_comments) > self.max_chars:
						print(f"\nSkipping {file_path} as it is too long.")
						continue

					count += 1
					# Get the file path from the project root
					path = os.path.relpath(file_path, self.project_path)
					suggestions = self.submit_code_to_chatgpt(code_no_comments, path)

					if suggestions:
						# Check if the suggestions are the same as the code we submitted
						if suggestions == code_no_comments or suggestions.lower() == "no changes proposed":
							print(f"\nNo suggestions found for {file_path}")
							continue

						with open(diff_file_path, "w", encoding="utf-8") as diff_file:
							diff_file.write(suggestions)
						print(f"\nSuggestions saved to {diff_file_path}")
					else:
						print(f"\nChatGPT did not return suggestions for {file_path}")
			except Exception as e:
				print(f"\nError processing file {file_path}: {e}")

def main(args):
	try:
		try:
			with open(args.settings, "r", encoding="utf-8") as file:
				settings = yaml.safe_load(file)
				openai_api_key = settings['lint']["key"]
		except Exception as e:
			print(f"Error loading settings: {e}")
			return

		bugfixer = ChatGPTBugFixer(openai_api_key, args)
		bugfixer.process_python_files()
	except KeyboardInterrupt:
		print("Exiting...")

if __name__ == "__main__":
	parser = argparse.ArgumentParser(description="Check Python files for bugfixes and improvements using ChatGPT")
	parser.add_argument("--settings", default="conf/settings.yaml", help="Path to the settings.yaml file")
	parser.add_argument("--path", "-p", default="../lib/", help="Path to the project folder")
	parser.add_argument("--max", "-m", default=0, type=int, help="Maximum number of files to process (default: 0, i.e. no limit)")
	parser_args = parser.parse_args()

	main(parser_args)
