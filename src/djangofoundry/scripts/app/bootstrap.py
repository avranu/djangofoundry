"""
*********************************************************************************************************************
*                                                                                                                      *
*                                                                                                                      *
*                                                                                                                      *
*                                                                                                                      *
* -------------------------------------------------------------------------------------------------------------------- *
*                                                                                                                      *
*    METADATA:                                                                                                         *
*                                                                                                                      *
*        File:    bootstrap.py                                                                                         *
*        Project: django-foundry                                                                                       *
*        Version: 0.0.10                                                                                               *
*        Created: 2025-03-17                                                                                           *
*        Author:  Jess Mann                                                                                            *
*        Email:   jess@jmann.me                                                                                        *
*        Copyright (c) 2025 Jess Mann                                                                                  *
*                                                                                                                      *
* -------------------------------------------------------------------------------------------------------------------- *
*                                                                                                                      *
*    LAST MODIFIED:                                                                                                    *
*                                                                                                                      *
*        2025-03-17     By Jess Mann                                                                                   *
*                                                                                                                      *
*********************************************************************************************************************
"""
from __future__ import annotations

import logging
import os
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Optional

import psutil

from djangofoundry.scripts.utils.exceptions import DbStartError
from djangofoundry.scripts.utils.settings import DEFAULT_SETTINGS_PATH

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s', handlers=[logging.StreamHandler()])
logger = logging.getLogger(__name__)

FILES_PATH = Path(__file__).parents[2] / "files"

class Bootstrap:
    """
    Handles project setup tasks for a Django project using modern tools like uv and bun.
    """

    def __init__(self, project_name: str | None = None, directory: str = '.'):
        if not project_name:
            # Get the name of the current directory
            project_name = os.path.basename(os.path.abspath(directory))
        self.project_name = project_name
        self.directory = directory
        self.src_dir = os.path.join(directory, 'src')
        self.project_src_dir = os.path.join(self.src_dir, project_name)
        super().__init__()

    def check_environment(self) -> None:
        """
        Verify the environment meets requirements for project setup.
        """
        # Check Python version
        if sys.version_info < (3, 12):
            raise EnvironmentError("Python 3.12 or above is required.")
        logger.debug("Python version check passed.")

        # Check directory permissions
        if not os.access(self.directory, os.W_OK):
            raise EnvironmentError("The provided directory does not have write permissions.")
        logger.debug("Directory permissions check passed.")

        # Check disk space
        disk_usage = psutil.disk_usage('/')
        if disk_usage.free < 1 * 10**9:  # less than 1GB
            raise EnvironmentError(f"Insufficient disk space. At least 1GB is required. {disk_usage.free / 10**9:.2f}GB available.")
        logger.debug("Disk space check passed.")

        # Check RAM
        ram_usage = psutil.virtual_memory()
        if ram_usage.available < 0.5 * 10**9:  # less than 1/2GB
            raise EnvironmentError(f"Insufficient RAM. At least 0.5GB is required. {ram_usage.available / 10**9:.2f}GB available.")
        logger.debug("RAM check passed.")

        # Check for required tools
        for tool in ["uv", "django-admin", "direnv"]:
            if not shutil.which(tool):
                raise EnvironmentError(f"Required tool '{tool}' is not installed.")
            
        logger.info("✅ All environment checks passed.")

    def run_command(self, cmd: list[str], cwd: Optional[str] = None) -> str:
        """
        Run a command and return its output.
        """
        current_dir = os.getcwd()
        try:
            if cwd:
                os.chdir(cwd)
            
            logger.debug(f"Running command: {' '.join(cmd)}")
            process = subprocess.run(
                cmd,
                check=True,
                capture_output=True,
                text=True
            )
            if process.stdout:
                logger.debug(process.stdout)
            return process.stdout or ""
        except subprocess.CalledProcessError as e:
            logger.error(f"Command failed: {' '.join(cmd)}")
            logger.error(f"Error output: {e.stderr}")
            raise
        finally:
            if cwd:
                os.chdir(current_dir)

    def create_project_structure(self) -> None:
        """
        Create the initial project directory structure.
        """
        logger.info("Creating project structure...")
        os.makedirs(self.directory, exist_ok=True)
        os.makedirs(os.path.join(self.directory, "tests"), exist_ok=True)
        
        # Create .env file
        env_content = f"""AIDER_OPENAI_API_KEY=example
AIDER_ANTHROPIC_API_KEY=example
AIDER_MODEL="anthropic/claude-3-7-sonnet-20250219"
PYPI_TOKEN=example
UV_LINK_MODE="copy"
PYTHONDONTWRITEBYTECODE=1
PYTHONPATH="./src/{self.project_name}/:$PYTHONPATH"
DEBUG=TRUE
SECRET_KEY=django-insecure-{os.urandom(24).hex()}
DJANGO_SETTINGS_MODULE="{self.project_name}.settings"
"""
        with open(os.path.join(self.directory, ".env"), "w") as f:
            f.write(env_content)
        
        # Create .envrc file
        envrc_content = """dotenv"""
        with open(os.path.join(self.directory, ".envrc"), "w") as f:
            f.write(envrc_content)

        self.run_command(['direnv', 'allow'], cwd=self.directory)
            
        logger.info("✅ Project structure created successfully")

    def initialize_project(self) -> None:
        """
        Initialize the project using uv and bun.
        """
        logger.info("Initializing project with uv...")
        
        # Initialize with uv
        self.run_command([
            "uv", "init",
            f"--name={self.project_name}",
            "--package",
            "--app",
            "--description", f"A scaffold for the {self.project_name} project.",
            "--vcs", "git",
            "--build-backend", "hatch",
            "-p", "3.12"
        ], cwd=self.directory)

        # Append files/pyproject.toml to the end of ./pyproject.toml
        project_pyproject = Path(self.directory) / "pyproject.toml"
        foundry_pyproject = FILES_PATH / "pyproject.toml"
        with open(project_pyproject, "a") as project_file:
            with open(foundry_pyproject, "r") as foundry_file:
                project_file.write(foundry_file.read())
        
        # Copy package.json from files/ to project root
        foundry_package_json = FILES_PATH / "package.json"
        package_json = Path(self.directory) / "package.json"
        shutil.copy2(foundry_package_json, package_json)

        # Use sed to replace {package_name} with the project name in both files
        self.run_command([
            "sed", "-i", f"s/{{package_name}}/{self.project_name}/g",
            str(project_pyproject), str(package_json)
        ])

        # Add .vscode/settings.json and .hypothesis to .gitignore
        with open(os.path.join(self.directory, ".gitignore"), "a") as gitignore_file:
            gitignore_file.write(".vscode/settings.json\n")
            gitignore_file.write(".hypothesis\n")

        # Create empty "logs" directory
        os.makedirs(os.path.join(self.directory, "logs"), exist_ok=True)
        os.makedirs(os.path.join(self.directory, "docs"), exist_ok=True)
        
        logger.info("✅ Project initialized successfully")

    def create_venv(self) -> None:
        """
        Create a virtual environment using uv.
        """
        logger.info("Creating virtual environment...")
        self.run_command(["uv", "venv", ".venv"], cwd=self.directory)
        logger.info("✅ Virtual environment created successfully")

    def install_dependencies(self) -> None:
        """
        Install project dependencies using uv.
        """
        logger.info("Installing Django and project dependencies...")

        packages = [
            "colorlog",
            "dateparser",
            "Django",
            "djangofoundry",
            "django-auto-prefetch",
            "django-cors-headers",
            "django-cprofile-middleware",
            "django-dirtyfields",
            "django-picklefield",
            "django-extensions",
            "django-filter",
            "django-lifecycle",
            "django-pandas",
            "django-postgres-extra",
            "djangorestframework",
            "faker",
            "httpx",
            "humanize",
            "jinja2",
            "multipledispatch",
            "openai",
            "orjson",
            "psutil",
            "postgres",
            "pydantic",
            "pydantic-settings",
            "python-dotenv",
            "requests",
            "rich",
            "statsmodels",
            "typing-extensions",
        ]
        
        # Core dependencies
        self.run_command(["uv", "add"] + packages, cwd=self.directory)
        
        # Development dependencies
        dev_tools = [
            "ruff", "pyright", "mypy", "pre-commit",
            "bandit", "coverage", "hypothesis",
            "pydoctor", "pytest", "pytest-cov", "flake8",
            "model-bakery",
        ]
        self.run_command(["uv", "add", "--dev"] + dev_tools, cwd=self.directory)
        self.run_command(["uv", "sync", "--all-groups"], cwd=self.directory)
        
        logger.info("✅ Dependencies installed successfully")

    def setup_django_project(self) -> None:
        """
        Set up the Django project using django-admin.
        """
        logger.info("Setting up Django project...")
        
        # Remove generated __init__.py file, so django can overwrite it
        init_file = os.path.join(self.project_src_dir, "__init__.py")
        if os.path.exists(init_file):
            os.remove(init_file)
            logger.debug(f"Removed {init_file}")
            
        # Create Django project
        self.run_command([
            "django-admin", "startproject",
            self.project_name,
            self.project_src_dir
        ], cwd=self.directory)

        # Recursively copy the files from files/lib and files/dashboard to src/{project_name}/
        FILES = {
            (FILES_PATH / "lib", self.project_src_dir),
            (FILES_PATH / "dashboard", self.project_src_dir),
            (FILES_PATH / ".github", self.directory),
            (FILES_PATH / ".pre-commit-config.yml", self.directory),
        }
        for src_file, dest_dir in FILES:
            self.run_command([
                "cp", "-r", str(src_file), str(dest_dir)
            ])
            
        # Create the main app
        os.makedirs(self.project_src_dir, exist_ok=True)
        self.run_command([
            "django-admin", "startapp", "dashboard",
            os.path.join(self.project_src_dir, "dashboard")
        ], cwd=self.directory)

        # Remove models.py, tests.py, views.py
        for file in ["models.py", "tests.py", "views.py"]:
            os.remove(os.path.join(self.project_src_dir, "dashboard", file))
            
        # Replace src/{project_name}/{project_name}/urls.py with files/urls.py
        os.remove(os.path.join(self.project_src_dir, self.project_name, "urls.py"))
        shutil.copy2(FILES_PATH / "urls.py", os.path.join(self.project_src_dir, self.project_name, "urls.py"))

        # Replace {project_name} with the project name in all *.py and *.json files
        self.run_command([
            "find", self.project_src_dir, "-type", "f",
            "(", "-name", "*.py", "-o", "-name", "*.json", ")",
            "-exec", "sed", "-i", f"s/{{project_name}}/{self.project_name}/g", "{}", "+"
        ])

        
        logger.info("✅ Django project setup completed")

    def setup_db(self) -> None:
        """
        Set up the database for the Django project.
        """
        logger.info("Setting up database...")
        
        # Create the database
        self.run_command([
            "python", "manage.py", "migrate"
        ], cwd=self.project_src_dir)

    def setup(self) -> None:
        """
        Run the complete project setup process.
        """
        try:
            self.check_environment()
            self.create_project_structure()
            self.initialize_project()
            self.create_venv()
            self.install_dependencies()
            self.setup_django_project()
            self.setup_db()
            
            logger.info(f"🎉 Project {self.project_name} has been successfully set up!")
            logger.info("To activate the environment: source .venv/bin/activate")
            logger.info(f"To run the server: cd {self.project_src_dir} && python manage.py runserver")
            
        except Exception as e:
            logger.error(f"Project setup failed: {e}")
            raise

def main():
    """
    Main entry point for the command-line interface.
    """
    try:
        import argparse
        
        parser = argparse.ArgumentParser(description='Bootstrap Django application')
        parser.add_argument('-p', '--project-name', default=None, help='Project name')
        parser.add_argument('-d', '--directory', default='.', help='Project directory')
        parser.add_argument('-s', '--settings', default=DEFAULT_SETTINGS_PATH, help='Settings file')
        parser.add_argument('--verbose', action='store_true', help='Enable verbose output')
        
        args = parser.parse_args()
        
        bootstrap = Bootstrap(args.project_name, args.directory)
        bootstrap.setup()

        if args.verbose:
            logger.setLevel(logging.DEBUG)

    except KeyboardInterrupt:
        logger.info('Shutting down...')
        sys.exit(0)
    except DbStartError:
        logger.error('Could not start DB. Cannot continue')
        sys.exit(1)
    except EnvironmentError as e:
        logger.error(f'Environment error: {e}')
        sys.exit(1)
    except Exception as e:
        logger.error(f"Error: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()
