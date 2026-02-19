"""*****************************************************************************
*                                                                             *
* Metadata:                                                                   *
*                                                                             *
* 	File: app.py                                                               *
* 	Project: django-foundry                                                    *
* 	Created: 19 Oct 2023                                                       *
* 	Author: Jess Mann                                                          *
* 	Email: jess.a.mann@gmail.com                                               *
*                                                                             *
* 	-----                                                                      *
*                                                                             *
* 	Last Modified: Sat Oct 28 2023                                             *
* 	Modified By: Jess Mann                                                     *
*                                                                             *
* 	-----                                                                      *
*                                                                             *
* 	Copyright (c) 2023 Jess Mann                                               *
****************************************************************************"""
# !/usr/bin/env python

# Generic imports
from __future__ import annotations

import argparse
from collections.abc import Callable
import getpass
import json
import logging
import os
import platform
import re
import shutil
import subprocess
import sys
from typing import Any, Optional

from jinja2 import Environment, FileSystemLoader
import psutil

from djangofoundry.scripts.app.actions import Actions
from djangofoundry.scripts.db.db import Db

# Our imports
from djangofoundry.scripts.utils.exceptions import DbStartError, UnsupportedCommandError
from djangofoundry.scripts.utils.settings import DEFAULT_SETTINGS_PATH, Settings

logging.basicConfig(level=logging.DEBUG, stream=sys.stdout)
logger = logging.getLogger(__name__)


class App:
    """
    Our main application class. This script allows us to start, stop, and restart our django server.
    """

    _command: Actions
    _output_buffer: str = ""
    project_name: str
    directory: str
    frontend_dir: str
    backend_dir: str
    settings: Settings | None = None

    def __init__(
        self,
        project_name="myproject",
        author_name=None,
        settings=None,
        directory: str = ".",
        frontend_dir="frontend",
        backend_dir="backend",
    ):
        self.project_name = project_name
        self.directory = directory
        if frontend_dir[0] == "/":
            self.frontend_dir = frontend_dir
        else:
            self.frontend_dir = directory + "/" + frontend_dir
        if backend_dir[0] == "/":
            self.backend_dir = backend_dir
        else:
            self.backend_dir = directory + "/" + backend_dir
        self.author_name = author_name or getpass.getuser()
        self.settings = settings

    @property
    def command(self) -> Actions:
        """
        Get the currently executing command. This is typically set by self.perform()
        """
        if self._command is None:
            raise ValueError("Command has not been set yet")
        return self._command

    def get_argument(self, argument_name: str, args: tuple, kwargs: dict) -> Any:
        """
        Retrieves an argument from args/kwargs.

        This is useful for methods like self.perform() where we want to pass arguments to an arbitrary method, which may be different per command.

        Args:
                argument_name (str):
                        The name of the argument to retrieve
                args (tuple):
                        The list of arguments passed to the method
                kwargs (dict):
                        The dictionary of keyword arguments passed to the method

        Returns:
                The argument value, if it exists. Otherwise, None.

        Examples:
                >>> class Foo(App):
                >>> 	def change_page(self, *args, **kwargs):
                >>> 		argument = self.get_argument('page_name', args, kwargs)
                >>> 		print('page_name = ' + argument)
                >>> foo = Foo()
                >>> foo.change_page('home')
                page_name = home
        """
        if len(args) == 1:
            return args[0]
        return kwargs.get(argument_name)

    def create_venv(self, venv_name: str = "venv") -> bool:
        """
        Create a virtual environment for our project and enter it.
        """
        logger.info("Creating virtual environment...")
        try:
            subprocess.check_output(["python", "-m", "venv", "venv"], stderr=subprocess.STDOUT)
        except subprocess.CalledProcessError as e:
            logger.error(f"Could not create virtual environment: {e.output}")
            return False

        logger.info("Activating virtual environment...")
        try:
            # If windows...
            if platform.system() == "Windows" or platform.system() == "win32":
                activate_command = os.path.join(venv_name, "Scripts", "activate")
            else:
                activate_command = os.path.join(venv_name, "bin", "activate")

            subprocess.check_call([f". {activate_command}"], shell=True)
        except subprocess.CalledProcessError as e:
            logger.error(f"Could not activate virtual environment: {e.output}")
            return False

        return True

    def pip_install(self, package_name: str) -> bool:
        """
        Install a python package using pip, and add it (with version) to requirements.txt.

        Args:
                pip_package (str): The name of the package(s) to install, separated by a space

        Returns:
                bool: True if the package was installed successfully, False otherwise.

        Examples:
                >>> app = App()
                >>> app.pip_install('requests')
                True

                >>> app.pip_install('requests==2.26.0')
                True
        """
        # If the package_name contains multiple packages, split them and install them individually
        if " " in package_name:
            for single_package_name in package_name.split(" "):
                if not self.pip_install(single_package_name):
                    return False
            return True

        # If requirements.txt doesn't exist, create it
        if not os.path.exists("requirements.txt"):
            logger.info("Creating requirements.txt...")
            with open("requirements.txt", "w") as f:
                f.write("")

        # Check if the package is already in requirements.txt
        # TODO: this ignores version numbers (therefore not handling updates)
        with open("requirements.txt") as f:
            if package_name in f.read():
                logger.info(f"{package_name} already in requirements.txt. Skipping pip install.")
                return True

        # Install the package, capture output so that we can determine the version number of the package
        logger.info(f"Installing {package_name}...")
        install_output = subprocess.check_output(
            [sys.executable, "-m", "pip", "install", package_name], stderr=subprocess.STDOUT
        ).decode("utf-8")

        # Grab the version number from the output
        output = re.search(r"Successfully installed (.*)", install_output)

        if not output:
            logger.warning(f"Could not find a version number after installing {package_name}. Output: {install_output}")
            return False

        version = output.group(1).split("-")[-1]

        if version is None:
            logger.warning(f"Could not determine version number for {package_name}")
            return False

        # Ensure version is a valid version number
        if not re.match(r"^\d+\.\d+\.\d+$", version):
            logger.warning(f"Version number for {package_name} is not valid: {version}")
            return False

        # Add package (and version #) to requirements.txt.
        logger.info(f"Adding {package_name} to requirements.txt...")
        with open("requirements.txt", "a") as f:
            f.write(f"{package_name}>={version}\n")

        return True

    def django_createapp(self, name: str):
        """
        Creates a new app in django (similar to python manage.py startapp) but with our custom changes to the default app structure.
        """

        self.run_subprocess(["python", "manage.py", "startapp", name])

        try:
            # Within the app dir, remove the models.py file, and create a models directory with __init__.py inside it
            os.chdir(os.path.join(self.project_name, "dashboard"))
            os.remove("models.py")

            # Create directories for models, controllers, and templates
            # dir_name => create __init__.py
            dirs = {"models": True, "controllers": True, "templates": False}
            for dir_name, create_init in dirs.items():
                os.makedirs(dir_name, exist_ok=True)
                if create_init:
                    with open(os.path.join(dir_name, "__init__.py"), "w") as f:
                        f.write("")

            # Copy all files from ../templates/app_templates (relative to this file) to {name}/templates/{name}/
            templates_dir = os.path.join(os.path.dirname(os.path.realpath(__file__)), "app_templates")
            shutil.copytree(templates_dir, os.path.join(name, "templates", name))

            # Render ../templates/IndexController.py.jinja and save it to ./controllers/IndexController.py
            env = Environment(loader=FileSystemLoader("templates/jinja/IndexController"))

            controller_dir = f"{self.backend_dir}/{name}/controllers/"
            os.makedirs(controller_dir, exist_ok=True)

            for template_name in env.list_templates():
                template = env.get_template(template_name)
                rendered_template = template.render(controller_name="IndexController")
                output_file = os.path.join(controller_dir, template_name.replace(".jinja", ".py"))
                with open(output_file, "w") as file:
                    file.write(rendered_template)
        finally:
            os.chdir(self.backend_dir)

    def django_setup(self) -> str:
        """
        Setup the Django project and app with given names.

        Note: This is a work in progress.

        Returns:
                A string indicating the status of the setup.
        """
        try:
            os.makedirs(self.backend_dir, exist_ok=True)
            # Switch to the backend directory before running Django commands
            os.chdir(self.backend_dir)
            self.run_subprocess(["pip", "install", "django"])
            self.run_subprocess(["django-admin", "startproject", self.project_name, "backend"])
            self.django_createapp("dashboard")

        finally:
            # Switch back to the original directory
            os.chdir(self.directory)

        return f"Django setup completed for {self.project_name}"

    def setup_frontend(self) -> str:
        """
        Setup the frontend (including package.json) for an arbitrary frontend framework.

        Returns:
                A string indicating the status of the setup.
        """
        try:
            os.makedirs(self.frontend_dir, exist_ok=True)
            # Switch to the frontend directory before installing npm packages
            os.chdir(self.frontend_dir)
            self.run_subprocess(["npm", "init", "-y"])

            with open("package.json", encoding="utf-8") as f:
                data = json.load(f)

            # Modify the existing package.json file to include our params
            data["name"] = self.project_name
            data["version"] = "1.0.0"
            data["description"] = f"{self.project_name} - a Django project"
            data["main"] = "index.js"
            data["scripts"] = {"test": 'echo "Error: no test specified" && exit 1'}
            data["author"] = getpass.getuser()
            data["license"] = "BSD-3-Clause"

            with open("package.json", "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)

            # TODO 3 sparate npm commands can likely be consolidated into 2 or 1.
            self.run_subprocess(["npm", "install"])

            # Create a dashboard directory, with a ts and sass subdirectory
            os.makedirs("dashboard", exist_ok=True)
            os.makedirs("dashboard/ts", exist_ok=True)
            os.makedirs("dashboard/sass", exist_ok=True)
        finally:
            os.chdir(self.directory)  # Switch back to the original directory

        return f"Frontend setup completed for {self.project_name}"

    def append_django_apps(self, app_name: str) -> bool:
        """
        Add the app to the INSTALLED_APPS list in the settings/base.py file
        """
        settings_file = f"{self.backend_dir}/{self.project_name}/settings/base.py"

        # Load the entire settings/base.py file into memory
        # TODO try catch
        with open(settings_file) as f:
            contents = f.read()

            # Get the installed apps list
            codeblock = re.search(r"INSTALLED_APPS = \[(.*)\]", contents, re.DOTALL)
            if not codeblock:
                # TODO better exception
                raise Exception(f"Could not find INSTALLED_APPS in {settings_file}")

            installed_apps = codeblock.group(1)
            if not installed_apps:
                # TODO better exception
                raise Exception(f"No apps found in INSTALLED_APPS. Settings file: {settings_file}")

            installed_apps = installed_apps.strip()

            # Check if the app is already in INSTALLED_APPS
            if re.search(rf"'{app_name}'", installed_apps):
                logger.info(f"{app_name} is already in INSTALLED_APPS")
                return True

            # Modify contents with regex to include the app at the end of the list
            contents = re.sub(
                r"INSTALLED_APPS = \[(.*)\]", rf"INSTALLED_APPS = [\1, \'{app_name}\']", contents, re.DOTALL
            )

        # Write the new contents
        with open(settings_file, "w") as f:
            f.write(contents)

        return True

    def append_django_middleware(self, middleware_name: str) -> bool:
        """
        Add the middleware to the MIDDLEWARE list in the settings/base.py file
        """
        settings_file = f"{self.backend_dir}/{self.project_name}/settings/base.py"

        # Load the entire settings/base.py file into memory
        # TODO try catch
        with open(settings_file) as f:
            contents = f.read()

            # Get the installed apps list
            codeblock = re.search(r"MIDDLEWARE = \[(.*)\]", contents, re.DOTALL)
            if not codeblock:
                # TODO better exception
                raise Exception(f"Could not find MIDDLEWARE in {settings_file}")

            middleware = codeblock.group(1)
            if not middleware:
                # TODO better exception
                raise Exception(f"No middleware found in MIDDLEWARE. Settings file: {settings_file}")

            middleware = middleware.strip()

            # Check if the middleware is already in MIDDLEWARE
            if re.search(rf"'{middleware_name}'", middleware):
                logger.info(f"{middleware_name} is already in MIDDLEWARE")
                return True

            # Modify contents with regex to include the middleware at the end of the list
            contents = re.sub(
                r"MIDDLEWARE = \[(.*)\]", rf"MIDDLEWARE = [\1, \'{middleware_name}\']", contents, re.DOTALL
            )

        # Write the new contents
        with open(settings_file, "w") as f:
            f.write(contents)

        return True

    def svelte_setup(self) -> str:
        """
        Setup the svelte project and app
        """
        # TODO
        return "Svelte setup skipped."

    def bun_setup(self) -> str:
        """
        Setup bun
        """
        # TODO
        return "Bun setup skipped."

    def nuxt_setup(self) -> str:
        """
        Setup the Nuxt project and app with given names.

        Returns:
                A string indicating the status of the setup.
        """
        self.setup_frontend()

        # Handle dependencies for nuxt
        self.run_subprocess(["npm", "install", "-y", "@nuxtjs/auth", "create-nuxt-app"])
        self.pip_install(
            "django-rest-framework dj-rest-auth django-allauth django-cors-headers djangorestframework-simplejwt"
        )

        # Setup the Nuxt project
        self.run_subprocess(["npx", "create-nuxt-app", self.frontend_dir])

        # Append necessary django apps to the settings file
        for app_name in ["corsheaders", "rest_framework"]:
            self.append_django_apps(app_name)

        # Append middleware to the settings file
        for middleware_name in ["corsheaders.middleware.CorsMiddleware"]:
            self.append_django_middleware(middleware_name)

        """
        Remaining tasks to do:
        * Add the following lines to enable JWT Authentication:
        REST_FRAMEWORK = {
            'DEFAULT_AUTHENTICATION_CLASSES': (
                'rest_framework_simplejwt.authentication.JWTAuthentication',
            ),
        }

        * Configure Django URLs
            urlpatterns = [
                path('admin/', admin.site.urls),
                path('api/v1/', include('dj_rest_auth.urls')),
            ]

        * Add the following lines to nuxt.config.js
            modules: [
                '@nuxtjs/auth',
            ],
            auth: {
                strategies: {
                    local: {
                        endpoints: {
                            login: { url: '/api/v1/login/', method: 'post', propertyName: 'token' },
                            logout: { url: '/api/v1/logout/', method: 'post' },
                            user: { url: '/api/v1/user/', method: 'get', propertyName: 'user' }
                        },
                        tokenRequired: true,
                        tokenType: 'Bearer',
                    }
                }
            }

        * For new nuxtjs components:
            this.$auth.loginWith('local', {
                data: {
                    username: this.username,
                    password: this.password
                }
            })
        """
        return f"Nuxt setup completed for {self.project_name}"

    def install_dependencies(self) -> None:
        """
        Check if npm is installed and call install_npm() if it's not.

        Returns:
                None
        """
        if not shutil.which("npm"):
            logger.info("NPM not found. Attempting to install...")
            self.install_npm()

    def install_npm(self) -> str:
        """
        Attempt to install npm on the system.

        Returns:
                A string indicating the status of the installation.
        """
        os_name = platform.system()

        # If ubuntu, install with apt
        if os_name == "Linux" and shutil.which("apt"):
            try:
                self.run_subprocess(["sudo", "apt", "install", "npm", "npx"])
                return "npm installed successfully on Ubuntu"
            except subprocess.CalledProcessError as process_e:
                raise OSError(f"Error installing npm on Ubuntu: {process_e}") from process_e

        # Otherwise, check for other variants of linux
        if os_name in ["Linux", "Darwin"]:
            try:
                self.run_subprocess(["curl", "https://www.npmjs.com/install.sh", "|", "sh"])
                return "npm installed successfully on Linux or macOS"
            except subprocess.CalledProcessError as process_e:
                raise OSError(f"Error installing npm on Linux or macOS: {process_e}") from process_e

        if os_name == "Windows":
            try:
                self.run_subprocess(
                    [
                        "powershell",
                        "-Command",
                        'iex (New-Object Net.WebClient).DownloadString("https://www.npmjs.com/install.ps1")',
                    ]
                )
                return "npm installed successfully on Windows"
            except subprocess.CalledProcessError as process_e:
                raise OSError(f"Error installing npm on Windows: {process_e}") from process_e

        raise OSError("Unsupported operating system")

    def check_environment(self) -> None:
        """
        Check the environment to make sure the setup will run smoothly.

        Returns:
                None

        Raises:
                EnvironmentError: If the environment is not suitable for running the setup.
                OSError: If the operating system is not supported.
        """
        # Check Python version
        if sys.version_info < (3, 10):
            raise OSError("Python 3.10 or above is required.")
        logger.debug("Python version check passed.")

        # Check directory permissions
        if not os.access(self.directory, os.W_OK):
            raise OSError("The provided directory does not have write permissions.")
        logger.debug("Directory permissions check passed.")

        # Check disk space
        disk_usage = psutil.disk_usage("/")
        if disk_usage.free < 10**9:  # less than 1GB
            raise OSError("Insufficient disk space. At least 1GB is required.")
        logger.debug("Disk space check passed.")

        # Check RAM
        ram_usage = psutil.virtual_memory()
        if ram_usage.available < 10**6:  # less than 1MB
            raise OSError("Insufficient RAM. At least 1MB is required.")
        logger.debug("RAM check passed.")

        logger.info("All environment checks passed.")

    def confirm_setup(self) -> None:
        """
        Confirm the setup has been completed successfully.

        Returns:
                None

        Raises:
                EnvironmentError: If the setup was not completed successfully.
        """
        # Check for package dependencies
        dependencies = ["npm"]
        for dependency in dependencies:
            if not shutil.which(dependency):
                raise OSError(f"The {dependency} command isn't available. Please install it.")
        logger.debug("npm dependency check passed.")

        # Check for pip dependencies via imports
        dependencies = ["django", "psutil"]
        for dependency in dependencies:
            try:
                __import__(dependency)
            except ImportError as ie:
                raise OSError(f"The {dependency} package isn't available. Please install it.") from ie
        logger.debug("python dependency check passed.")

    def setup(self) -> None:
        """
        Setup Django project and apps with given names.

        Returns:
                None
        """
        os.makedirs(self.directory, exist_ok=True)

        self.check_environment()
        self.create_venv()
        self.install_dependencies()
        self.django_setup()
        self.svelte_setup()
        self.confirm_setup()

    def run(self, command: Actions, callback: Callable | None = None, *args, **kwargs) -> str:
        """
        Run a django command in a similar way to manage.py

        Args:
                command (str):
                        A command that django will accept. For example: runserver
                callback (Callable):
                        A function to call after the command completes.
                *args:
                        positional arguments to pass to django
                **kwargs:
                        named arguments to pass to django

        Returns:
                str: The output returned by django.

        Raises:
                ValueError: If the subprocess doesn't return any output.
        """
        # Run the django dev server in a subprocess, and pipe output to the command.stdout property.
        try:
            # Clear the output buffer for this run
            self._output_buffer = ""

            # Subprocess wants each arg as a separate entry in a list... combine args into our known command string.
            script_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "../manage.py")
            input_str = ["python", script_path, f"{command}"] + list(args)

            with subprocess.Popen(input_str, stdout=subprocess.PIPE, encoding="utf-8") as process:
                if not process.stdout:
                    raise ValueError("No output from subprocess")

                # Stdout is a stream, so this acts like a while() loop as long as django is running.
                for line in process.stdout:
                    # Pass all output to our handler, which may trigger events.
                    self.handle_output(line)

                # Wait for output that may not have hit the stream yet. (TODO: This may not be necessary?)
                process.wait()

                # Issue our callback, as we're now finished.
                if callback is not None:
                    logger.debug("Issuing callback on completion")
                    callback(process)

        except KeyboardInterrupt:
            # Allow terminating the dev server from the command line.
            logger.info("Stopping server...")

        return self._output_buffer

    def run_subprocess(self, cmd_list: list[str], print_output: bool = True) -> None:
        """
        Run the subprocess with the given command list.

        Args:
                cmd_list (list[str]):
                        A list of strings to pass to the subprocess.
                print_output (bool):
                        Whether to print the output of the subprocess to the console.

        Raises:
                ValueError: If the subprocess has no output.
        """
        with subprocess.Popen(cmd_list, stdout=subprocess.PIPE, encoding="utf-8") as process:
            if not process.stdout:
                raise ValueError("No output from subprocess")

            for line in process.stdout:
                self.handle_output(line, print_output)
            process.wait()

    def run_typical_command(self, command: Actions, callback: Callable | None = None, *args, **kwargs) -> str:
        """
        Runs a command that requires our normal tool suite (such as the DB) to be running.

        Args:
                command (str):
                        A command that django will accept. For example: runserver
                callback (Callable):
                        A function to call after the command completes.
                *args:
                        positional arguments to pass to django
                **kwargs:
                        named arguments to pass to django

        Returns:
                str: The output returned by django
        """
        # Attempt to start the db first. If it fails, this will print output and exit.
        self._start_db()

        # Pass any command we asked for over to django.
        return self.run(command, callback, *args, **kwargs)

    def start(self) -> str:
        """
        Start the django app, and any other tools it depends on.

        Returns:
                str: The output returned by django
        """
        return self.run_typical_command(Actions.START)

    def test(self) -> str:
        """
        Run our unit and integration tests.

        Returns:
                str: The output returned by django
        """
        return self.run_typical_command(Actions.TEST, None, "--noinput", "--verbosity=0")

    def stop(self):
        """
        Stop any tools that were started via start(), including the django app.
        """
        raise NotImplementedError

    @property
    def status(self) -> bool:
        """
        Determine the status of our application.
        """
        server_process_names = ["runserver", "gunicorn", "daphne"]
        for process in psutil.process_iter(["name"]):
            if process.name() in server_process_names:
                return True

        return False

    def sync_browser(self):
        """
        Start a process to sync the browser with the application state.

        We currently use browser-sync for this. When our app files change, the browser will automatically refresh the page.
        """
        # Subprocess wants each arg as a separate entry in a list... combine args into our known command string.
        input_str = ["npm", "run", "serve"]
        logger.debug("Starting browsersync")
        with subprocess.Popen(input_str, stdout=subprocess.PIPE, encoding="utf-8", shell=True) as process:
            if not process.stdout:
                raise ValueError("No output from subprocess")

            # Stdout is a stream, so this acts like a while() loop as long as django is running.
            for line in process.stdout:
                # Pass all output to our handler, which may trigger events.
                self.handle_output(line)

            # Wait for output that may not have hit the stream yet. (TODO: This may not be necessary?)
            process.wait()

    def on_django_started(self) -> None:
        """
        Called when the django dev server is fully started.
        """
        # If we're trying to start our app, then run our next action
        if self.command == Actions.START:
            self.sync_browser()

    def handle_output(self, line: str, print_output: bool = True) -> None:
        """
        Called for each line of input from django.

        Args:
                line (str):
                        A line of output from django.
                print_output (bool):
                        Whether to print the output of the subprocess to the console.

        Raises:
                ValueError: If the subprocess has no output.
        """
        value = re.sub(r"[\n\r\\]+", "", line or "")
        self._output_buffer += f"\n{value}"
        if (value) != "" and print_output:
            print(value)

        match value.lower():
            case "quit the server with ctrl-break.":
                logger.debug("Django started successfully")
                self.on_django_started()

    def perform(self, command: Actions, *args, **kwargs) -> Any:
        """
        Perform an action given a (string) command

        Args:
                command (Actions): The action to perform.
                page_name (str): The name of the page to create.
                model_name (str): The name of the model to create.

        Returns:
                Any: The result of the action.
        """
        # Save the command for later
        self._command = command

        # Determine what method to run.
        match command:
            case Actions.START:
                # Start our entire app
                return self.start()
            case Actions.TEST:
                # Run tests
                return self.test()
            case Actions.SETUP:
                # Setup our app
                return self.setup()
            case Actions.STOP:
                # Stop our app
                return self.stop()
            case Actions.STATUS:
                # Determine the status of our app
                return self.status
            case Actions.INSTALL:
                # Install a python package using pip, and add it (with version) to requirements.txt.
                package_name = self.get_argument("package_name", args, kwargs)
                return self.pip_install(package_name)
            case Actions.PAGE:
                # Ensure we have either one *arg, or a page_name **kwarg
                page_name = self.get_argument("page_name", args, kwargs)

                if page_name:
                    return self.create_new_page(page_name)
                raise ValueError("Page name is required for 'page' action.")
            case Actions.MODEL:
                model_name: str = self.get_argument("model_name", args, kwargs)
                if model_name:
                    return self.create_new_model(model_name)
                raise ValueError("Model name is required for 'model' action.")
            case _:
                raise UnsupportedCommandError(f"Unknown command {command}.")

    def _start_db(self) -> None:
        """
        Call db.py to start the DB. This prints output and (under certain circumstances) exits.

        Returns:
                None
        """
        db = Db()
        if db.is_running():
            logger.debug("DB is already running")
        else:
            logger.info("Starting DB...")
            _result = db.start()

            if not db.is_running():
                raise DbStartError("DB not running after start")

    def create_new_page(self, page_name: str) -> None:
        """
        Create a new page in Django and the frontend.

        Args:
                page_name (str): The name of the page to create.

        Returns:
                None
        """
        try:
            self.create_frontend_component(page_name)
            self.setup_routing(page_name)
            self.create_django_controller(page_name)
            logging.info(f"Successfully created new page '{page_name}' in Django and the frontend.")
        except Exception as new_page_exception:
            logging.error(f"Failed to create new page '{page_name}': {new_page_exception}")

    def create_frontend_component(self, page_name: str) -> None:
        """
        Create a new frontend component.

        Args:
                page_name (str): The name of the page to create.

        Returns:
                None
        """
        try:
            # TODO
            # subprocess.run(["ng", "generate", "component", page_name], check=True)
            pass
        except subprocess.CalledProcessError as process_e:
            logging.error(f"Failed to create frontend component '{page_name}': {process_e}")
            raise

    def setup_routing(self, page_name: str) -> None:
        """
        Set up routing for the new frontend component.

        Args:
                page_name (str): The name of the page to create.

        Returns:
                None
        """
        # TODO

    def create_django_controller(self, page_name: str) -> None:
        """
        Create a new Django controller.

        Args:
                page_name (str): The name of the page to create.

        Returns:
                None
        """
        controllers_dir = f"{self.backend_dir}/controllers"
        os.makedirs(controllers_dir, exist_ok=True)

        controller_file = os.path.join(controllers_dir, f"{page_name}.py")
        try:
            with open(controller_file, "w", encoding="utf-8") as file:
                file.write("from django.shortcuts import render\n\n")
                file.write(f"def {page_name}_view(request):\n")
                file.write(f"	return render(request, '{page_name}.html')\n")
        except OSError as ioe:
            logging.error(f"Failed to create Django controller '{page_name}': {ioe}")
            raise

    def create_new_model(self, model_name: str) -> None:
        """
        Create a new Django model using Jinja2 templates.

        Args:
                model_name (str): The name of the model to create.

        Returns:
                None
        """
        env = Environment(loader=FileSystemLoader("templates/jinja/model"))

        model_dir = f"{self.backend_dir}/models/{model_name}"
        os.makedirs(model_dir, exist_ok=True)

        for template_name in env.list_templates():
            template = env.get_template(template_name)
            rendered_template = template.render(model_name=model_name)
            output_file = os.path.join(model_dir, template_name.replace(".jinja", ".py"))
            with open(output_file, "w") as file:
                file.write(rendered_template)


def main():
    try:
        parser = argparse.ArgumentParser(description="Setup and manage the Django application.")
        parser.add_argument("action", choices=[e.value for e in Actions], help="The action to perform.")
        parser.add_argument("-p", "--project-name", default="myproject", help="The name of the project.")
        parser.add_argument("-a", "--author-name", help="The name of the author.")
        parser.add_argument("-d", "--directory", default=".", help="The directory for the project.")
        parser.add_argument(
            "-f", "--frontend-dir", default="frontend", help="The directory for the frontend (relative to -d)."
        )
        parser.add_argument(
            "-b", "--backend-dir", default="backend", help="The directory for the backend (relative to -d)."
        )
        parser.add_argument("-s", "--settings", default=DEFAULT_SETTINGS_PATH, help="The settings file to use.")
        parser.add_argument("--page-name", help="The name of the page to create.")
        parser.add_argument("--model-name", help="The name of the model to create.")
        parser.add_argument("--package-name", help="The name of the package to create.")
        args = parser.parse_args()

        # Load settings
        settings = Settings(args.settings)

        app = App(args.project_name, args.author_name, settings, args.directory, args.frontend_dir, args.backend_dir)
        command = Actions(args.action)

        result = app.perform(
            command, page_name=args.page_name, model_name=args.model_name, package_name=args.package_name
        )
        if result is not None:
            print(f"App returned ({result})")

    except KeyboardInterrupt:
        logger.info("Shutting down server...")
        sys.exit(0)
    except DbStartError:
        logger.error("Could not start DB. Cannot continue")
        sys.exit(0)
    except OSError as env_error:
        logger.error(f"Cannot run script in the current environment. {env_error}")
        sys.exit(0)
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(0)


if __name__ == "__main__":
    """
    This code is only run when this script is called directly (i.e. python bin/app.py)
    """
    main()
