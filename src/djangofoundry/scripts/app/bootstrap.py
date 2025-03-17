"""*********************************************************************************************************************
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
*********************************************************************************************************************"""
from __future__ import annotations
import os
from pathlib import Path
import sys
import shutil
import subprocess
import logging
from djangofoundry.scripts.utils.exceptions import DbStartError
from djangofoundry.scripts.utils.settings import DEFAULT_SETTINGS_PATH
import psutil
from typing import Optional

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
            project_name = os.path.basename(directory)
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
        if ram_usage.available < 1 * 10**9:  # less than 2GB
            raise EnvironmentError(f"Insufficient RAM. At least 1GB is required. {ram_usage.available / 10**9:.2f}GB available.")
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
        env_content = """AIDER_OPENAI_API_KEY=example
AIDER_ANTHROPIC_API_KEY=example
AIDER_MODEL="anthropic/claude-3-7-sonnet-20250219"
PYPI_TOKEN=example
UV_LINK_MODE="copy"
PYTHONDONTWRITEBYTECODE=1
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
            "--description", "TODO",
            "--vcs", "git",
            "--build-backend", "hatch",
            "-p", "3.12"
        ], cwd=self.directory)

        # Append files/pyproject.toml to the end of ./pyproject.toml
        project_pyproject = Path(self.directory) / "pyproject.toml"
        foundry_pyproject = FILES_PATH / "pyproject.toml"
        with project_pyproject.open("a") as f:
            # Replace {project_name} with the project name
            content = foundry_pyproject.read_text().replace("{project_name}", self.project_name)
            f.write(content)
        
        # Copy package.json from files/ to project root
        # Replace {package_name} with the package name
        foundry_package_json = FILES_PATH / "package.json"
        package_json = Path(self.directory) / "package.json"
        package_json.write_text(foundry_package_json.read_text().replace("{package_name}", self.project_name))
        
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
        
        # Core dependencies
        self.run_command(["uv", "add", "django", "httpx", "pydantic", "typing-extensions", "djangofoundry"], cwd=self.directory)
        
        # Development dependencies
        dev_tools = [
            "ruff", "pyright", "mypy", "pre-commit",
            "bandit", "coverage", "hypothesis", 
            "pydoctor", "pytest", "pytest-cov", "flake8"
        ]
        self.run_command(["uv", "add", "--dev"] + dev_tools, cwd=self.directory)
        
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
        foundry_files = FILES_PATH / "lib"
        dashboard_files = FILES_PATH / "dashboard"
        for src_dir in [foundry_files, dashboard_files]:
            self.run_command([
                "cp", "-r", str(src_dir), self.project_src_dir
            ])

        # Replace {project_name} with the project name in all files
        self.run_command([
            "find", self.project_src_dir, "-type", "f", "-name", "*.py", 
            "-exec", "sed", "-i", f"s/{{project_name}}/{self.project_name}/g", "{}", "+"
        ])
            
        # Create the main app
        os.makedirs(self.project_src_dir, exist_ok=True)
        self.run_command([
            "django-admin", "startapp", "dashboard",
            os.path.join(self.project_src_dir, "dashboard")
        ], cwd=self.directory)
        
        logger.info("✅ Django project setup completed")

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
        parser.add_argument('-p', '--project-name', default='myproject', help='Project name')
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
