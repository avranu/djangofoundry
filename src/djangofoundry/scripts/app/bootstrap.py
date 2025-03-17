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
*        Version: 0.0.1                                                                                                *
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
import sys
import shutil
import subprocess
import logging
import psutil
from typing import Optional

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

class Bootstrap:
    """
    Handles project setup tasks for a Django project using modern tools like uv and bun.
    """
    def __init__(self, project_name: str = 'myproject', directory: str = '.'):
        self.project_name = project_name
        self.directory = directory
        self.src_dir = os.path.join(directory, 'src')
        self.project_src_dir = os.path.join(self.src_dir, project_name)

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
            raise EnvironmentError("Insufficient disk space. At least 1GB is required.")
        logger.debug("Disk space check passed.")

        # Check RAM
        ram_usage = psutil.virtual_memory()
        if ram_usage.available < 2 * 10**9:  # less than 2GB
            raise EnvironmentError("Insufficient RAM. At least 2GB is required.")
        logger.debug("RAM check passed.")

        # Check for required tools
        for tool in ["uv", "bun"]:
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
        envrc_content = """PATH_ADD src
dotenv
"""
        with open(os.path.join(self.directory, ".envrc"), "w") as f:
            f.write(envrc_content)
            
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
        
        # Remove generated __init__.py file
        init_file = os.path.join(self.project_src_dir, "__init__.py")
        if os.path.exists(init_file):
            os.remove(init_file)
            logger.debug(f"Removed {init_file}")
        
        # Initialize with bun
        logger.info("Initializing project with bun...")
        self.run_command(["bun", "init", "-y"], cwd=self.directory)
        
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
        self.run_command(["uv", "add", "django", "httpx"], cwd=self.directory)
        
        # Development dependencies
        dev_tools = [
            "ruff", "pyright", "mypy", "pre-commit", "pydantic", 
            "typing-extensions", "bandit", "coverage", "hypothesis", 
            "pydoctor", "pytest", "pytest-cov", "djangofoundry"
        ]
        self.run_command(["uv", "add", "--dev"] + dev_tools, cwd=self.directory)
        
        logger.info("✅ Dependencies installed successfully")

    def setup_django_project(self) -> None:
        """
        Set up the Django project using django-admin.
        """
        logger.info("Setting up Django project...")
        
        # Create Django project
        self.run_command([
            "django-admin", "startproject", 
            self.project_name, 
            self.project_src_dir
        ], cwd=self.directory)
        
        # Create the main app
        os.makedirs(os.path.join(self.project_src_dir, "apps"), exist_ok=True)
        self.run_command([
            "django-admin", "startapp", "dashboard",
            os.path.join(self.project_src_dir, "apps", "dashboard")
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
