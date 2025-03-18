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
*        File:    app.py                                                                                               *
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

#!/usr/bin/env python
from __future__ import annotations

import logging
import os
import re
import subprocess
import sys
from pathlib import Path
from typing import Any, Callable, Optional

import psutil

from djangofoundry.scripts.app.actions import Actions
from djangofoundry.scripts.db.db import Db

# Our imports
from djangofoundry.scripts.utils.exceptions import DbStartError, UnsupportedCommandError
from djangofoundry.scripts.utils.settings import DEFAULT_SETTINGS_PATH, Settings

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

class App:
    """
    Main application class for managing a Django server.
    Handles starting, stopping, testing, and other runtime operations.
    """

    _command: Optional[Actions] = None
    _output_buffer: str = ''
    
    def __init__(
        self,
        project_name: str = 'myproject',
        settings: Optional[Settings] = None,
        directory: str = '.',
        backend_dir: str = 'src'
    ):
        self.project_name = project_name
        self.directory = directory
        self.backend_dir = os.path.join(directory, backend_dir)
        self.settings = settings

    @property
    def command(self) -> Actions:
        """
        Get the currently executing command. This is typically set by self.perform()
        """
        if self._command is None:
            raise ValueError('Command has not been set yet')
        return self._command

    def get_argument(self, argument_name: str, args: tuple, kwargs: dict) -> Any:
        """
        Retrieves an argument from args/kwargs.
        
        This is useful for methods like self.perform() where we want to pass arguments 
        to an arbitrary method, which may be different per command.
        """
        if len(args) >= 1:
            return args[0]
        return kwargs.get(argument_name, None)
    
    def run(self, command: Actions, callback: Optional[Callable] = None, *args, **kwargs) -> str:
        """
        Run a django command similar to manage.py
        """
        try:
            # Clear the output buffer for this run
            self._output_buffer = ''

            # Build the command with manage.py
            manage_py = Path(self.backend_dir) / self.project_name / 'manage.py'
            input_str = ['python', str(manage_py), f'{command}'] + list(args)

            with subprocess.Popen(
                input_str,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True
            ) as process:
                if not process.stdout:
                    raise ValueError('No output from subprocess')

                # Process output line by line
                for line in process.stdout:
                    self.handle_output(line)

                process.wait()

                # Issue callback when finished
                if callback is not None:
                    logger.debug('Issuing callback on completion')
                    callback(process)

        except KeyboardInterrupt:
            logger.info('Stopping server...')

        return self._output_buffer

    def run_subprocess(self, cmd_list: list[str], print_output: bool = True) -> None:
        """
        Run a subprocess with the given command list.
        """
        with subprocess.Popen(
            cmd_list,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True
        ) as process:
            if not process.stdout:
                raise ValueError('No output from subprocess')

            for line in process.stdout:
                self.handle_output(line, print_output)
            process.wait()

    def run_typical_command(self, command: Actions, callback: Optional[Callable] = None, *args, **kwargs) -> str:
        """
        Run a command that requires the database to be running.
        """
        # Start the database first
        self._start_db()

        # Pass command to Django
        return self.run(command, callback, *args, **kwargs)

    def start(self) -> str:
        """
        Start the Django application and its dependencies.
        """
        return self.run_typical_command(Actions.START)

    def test(self) -> str:
        """
        Run the project's tests.
        """
        return self.run_typical_command(Actions.TEST, None, '--noinput', '--verbosity=0')

    def stop(self) -> None:
        """
        Stop the Django application and its dependencies.
        """
        # Find Django processes
        server_process_names = ["runserver", "gunicorn", "daphne"]
        killed = False
        
        for process in psutil.process_iter(['pid', 'name', 'cmdline']):
            try:
                if any(name in (process.info['cmdline'] or []) for name in server_process_names):
                    logger.info(f"Stopping Django process {process.info['pid']}")
                    psutil.Process(process.info['pid']).terminate()
                    killed = True
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                continue
        
        if not killed:
            logger.info("No Django processes found to stop")

    @property
    def status(self) -> bool:
        """
        Check if the Django application is running.
        """
        server_process_names = ["runserver", "gunicorn", "daphne"]
        for process in psutil.process_iter(['name', 'cmdline']):
            try:
                if any(name in (process.info['cmdline'] or []) for name in server_process_names):
                    return True
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                continue
        return False

    def handle_output(self, line: str, print_output: bool = True) -> None:
        """
        Process a line of output from subprocess.
        """
        value = re.sub(r'[\n\r\\]+', '', line or '')
        self._output_buffer += f'\n{value}'
        if value and print_output:
            print(value)

        if 'quit the server with ctrl-break' in value.lower():
            logger.debug('Django started successfully')
            self.on_django_started()

    def on_django_started(self) -> None:
        """
        Called when the Django server has fully started.
        """
        # If we're trying to start our app, sync the browser
        if self._command == Actions.START:
            self.sync_browser()

    def sync_browser(self) -> None:
        """
        Sync the browser with application changes using browser-sync.
        """
        logger.debug('Starting browsersync')
        with subprocess.Popen(
            ['bun', 'run', 'serve'],
            stdout=subprocess.PIPE,
            text=True
        ) as process:
            if not process.stdout:
                raise ValueError('No output from subprocess')

            for line in process.stdout:
                self.handle_output(line)
            process.wait()

    def _start_db(self) -> None:
        """
        Start the database if it's not already running.
        """
        db = Db()
        if db.is_running():
            logger.debug('DB is already running')
        else:
            logger.info('Starting DB...')
            _result = db.start()

            if not db.is_running():
                raise DbStartError('DB not running after start')

    def create_new_page(self, page_name: str) -> None:
        """
        Create a new page in Django.
        """
        try:
            self.create_django_controller(page_name)
            self.create_django_template(page_name)
            logger.info(f"Successfully created new page '{page_name}'")
        except Exception as e:
            logger.error(f"Failed to create new page '{page_name}': {e}")
            raise

    def create_django_controller(self, page_name: str) -> None:
        """
        Create a new Django controller (view).
        """
        controllers_dir = os.path.join(self.backend_dir, self.project_name, "apps", "dashboard", "views")
        os.makedirs(controllers_dir, exist_ok=True)

        controller_file = os.path.join(controllers_dir, f"{page_name}.py")
        with open(controller_file, "w", encoding="utf-8") as file:
            file.write("from django.shortcuts import render\n\n")
            file.write(f"def {page_name}_view(request):\n")
            file.write(f"    return render(request, 'dashboard/{page_name}.html')\n")

    def create_django_template(self, page_name: str) -> None:
        """
        Create a new Django template.
        """
        templates_dir = os.path.join(self.backend_dir, self.project_name, "apps", "dashboard", "templates", "dashboard")
        os.makedirs(templates_dir, exist_ok=True)

        template_file = os.path.join(templates_dir, f"{page_name}.html")
        with open(template_file, "w", encoding="utf-8") as file:
            file.write("{% extends 'base.html' %}\n\n")
            file.write("{% block title %}{{ title }}{% endblock %}\n\n")
            file.write("{% block content %}\n")
            file.write(f"<h1>{page_name.title()} Page</h1>\n")
            file.write("<p>This is a new page created with djangofoundry.</p>\n")
            file.write("{% endblock %}")

    def create_new_model(self, model_name: str) -> None:
        """
        Create a new Django model.
        """
        models_dir = os.path.join(self.backend_dir, self.project_name, "apps", "dashboard", "models")
        os.makedirs(models_dir, exist_ok=True)

        model_file = os.path.join(models_dir, f"{model_name.lower()}.py")
        with open(model_file, "w", encoding="utf-8") as file:
            file.write("from django.db import models\n\n")
            file.write(f"class {model_name.capitalize()}(models.Model):\n")
            file.write("    name = models.CharField(max_length=100)\n")
            file.write("    description = models.TextField(blank=True)\n")
            file.write("    created_at = models.DateTimeField(auto_now_add=True)\n")
            file.write("    updated_at = models.DateTimeField(auto_now=True)\n\n")
            file.write("    def __str__(self):\n")
            file.write("        return self.name\n")
        
        # Update the models __init__.py file to import the new model
        init_file = os.path.join(models_dir, "__init__.py")
        init_content = f"from .{model_name.lower()} import {model_name.capitalize()}\n"
        
        # Append to existing file or create new one
        if os.path.exists(init_file):
            with open(init_file, "a", encoding="utf-8") as file:
                file.write(init_content)
        else:
            with open(init_file, "w", encoding="utf-8") as file:
                file.write(init_content)

    def perform(self, command: Actions, *args, **kwargs) -> Any:
        """
        Perform an action based on the specified command.
        """
        # Save the command for later
        self._command = command

        # Determine what method to run
        match command:
            case Actions.START:
                return self.start()
            case Actions.TEST:
                return self.test()
            case Actions.STOP:
                return self.stop()
            case Actions.STATUS:
                return self.status
            case Actions.PAGE:
                page_name = self.get_argument('page_name', args, kwargs)
                if page_name:
                    return self.create_new_page(page_name)
                else:
                    raise ValueError("Page name is required for 'page' action.")
            case Actions.MODEL:
                model_name = self.get_argument('model_name', args, kwargs)
                if model_name:
                    return self.create_new_model(model_name)
                else:
                    raise ValueError("Model name is required for 'model' action.")
            case _:
                raise UnsupportedCommandError(f"Unknown command {command}.")


def main():
    """
    Main entry point for the command-line interface.
    """
    try:
        import argparse
        
        parser = argparse.ArgumentParser(description='Manage Django application')
        parser.add_argument('action', choices=[e.value for e in Actions], help='Action to perform')
        parser.add_argument('-p', '--project-name', default='myproject', help='Project name')
        parser.add_argument('-d', '--directory', default='.', help='Project directory')
        parser.add_argument('-s', '--settings', default=DEFAULT_SETTINGS_PATH, help='Settings file')
        parser.add_argument('--page-name', help='Page name for page creation')
        parser.add_argument('--model-name', help='Model name for model creation')
        
        args = parser.parse_args()
        
        # For setup action, use the Bootstrap class
        if args.action == 'setup':
            from djangofoundry.scripts.app.bootstrap import Bootstrap
            bootstrap = Bootstrap(args.project_name, args.directory)
            bootstrap.setup()
            return
            
        # For other actions, use the App class
        settings = Settings(args.settings) if args.settings else None
        app = App(args.project_name, settings, args.directory)
        command = Actions(args.action)
        
        result = app.perform(
            command,
            page_name=args.page_name,
            model_name=args.model_name
        )
        
        if result is not None:
            print(f'App returned: {result}')

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
