"""
	
Metadata:
	
File: imports.py
Project: django-foundry
Created Date: 14 Jun 2023
Author: Jess Mann
Email: jess.a.mann@gmail.com
	
-----
	
Last Modified: Wed Jun 14 2023
Modified By: Jess Mann
	
-----
	
Copyright (c) 2023 Jess Mann
"""
import argparse
import logging
import os
import re
import sys
from collections import defaultdict


class ImportProcessor:
    def __init__(self, path):
        self.path = path

    def find_files_with_patterns(self, pattern1, pattern2):
        matching_files = []

        for root, _, files in os.walk(self.path):
            for file in files:
                if not file.endswith('.py'):
                    continue

                file_path = os.path.join(root, file)
                try:
                    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                        lines = f.readlines()
                        for i, line in enumerate(lines):
                            if re.search(pattern1, line):
                                if any(re.search(pattern2, lines[j]) for j in range(i + 1, len(lines))):
                                    matching_files.append(file_path)
                                    break
                except Exception as e:
                    logging.error(f"Error reading file {file_path}: {e}")

        return matching_files

    def find_imports(self, file_path):
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
            imports = re.findall(r'^\s*(?:from|import) (\S+)', content, re.MULTILINE)
            return imports

    def find_circular_imports(self, ext='.py'):
        imports = defaultdict(set)
        for root, _, files in os.walk(self.path):
            for file in files:
                if not file.endswith(ext):
                    continue

                file_path = os.path.join(root, file)
                module_path = os.path.relpath(file_path, self.path).replace('\\', '/').rstrip(ext)

                for imported_module in self.find_imports(file_path):
                    imports[module_path].add(imported_module)

        visited = set()
        circular_imports = set()

        def visit(module, path):
            if module in visited:
                return

            visited.add(module)
            path = path + [module]

            for imported_module in imports[module]:
                if imported_module in path:
                    circular_imports.add(tuple(path[path.index(imported_module):] + [imported_module]))
                else:
                    visit(imported_module, path)

            visited.remove(module)

        for module in list(imports.keys()):
            visit(module, [])

        return circular_imports

def main():
    parser = argparse.ArgumentParser(description="Process Python imports")
    parser.add_argument("path", help="Directory path to search")
    parser.add_argument("--pattern1", help="First pattern to search")
    parser.add_argument("--pattern2", help="Second pattern to search")
    parser.add_argument("--loglevel", type=str, choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"], default="INFO", help="Set logging verbosity")
    parser.add_argument("-a", "--action", choices=["circular", "order"], default="circular", help="The action to perform. CIRCULAR, ORDER")

    args = parser.parse_args()

    logging.basicConfig(level=args.loglevel, format="%(levelname)s: %(message)s")

    search_path = args.path
    processor = ImportProcessor(search_path)

    if args.action == "circular":
        circular_imports = processor.find_circular_imports()

        if circular_imports:
            print("Circular imports found:")
            for chain in circular_imports:
                print(" -> ".join(chain))
        else:
            print("No circular imports found.")
    else:
        if not args.pattern1 or not args.pattern2:
            print("Both pattern1 and pattern2 are required for the 'order' action")
            sys.exit(1)

        pattern1 = args.pattern1
        pattern2 = args.pattern2

        matching_files = processor.find_files_with_patterns(pattern1, pattern2)

        for file in matching_files:
            print(file)

if __name__ == "__main__":
    main()
