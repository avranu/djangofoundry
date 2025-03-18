"""

Metadata:

File: memory.py
Project: Django Foundry
Created Date: 19 Apr 2023
Author: Jess Mann
Email: jess.a.mann@gmail.com

-----

Last Modified: Thu Apr 20 2023
Modified By: Jess Mann

-----

Copyright (c) 2023 Jess Mann
"""
import tracemalloc

import psutil
from django.http import JsonResponse
from django.shortcuts import render
from django.views import View


class MemoryMonitorView(View):
	"""
	Display the current memory usage of the application
	"""

	template_name = 'memory.html'

	def get(self, request, *args, **kwargs):
		return render(request, self.template_name, *args, **kwargs)


def memory_usage(request):
	"""
	Return the current memory usage of the application
	"""
	process = psutil.Process()
	mem_info = process.memory_info()
	total_memory_usage = mem_info.rss / (1024 * 1024)  # Convert to MB

	celery_processes = []
	for proc in psutil.process_iter():
		try:
			if "celery" in proc.name().lower():
				celery_processes.append(proc)
		except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
			pass

	celery_memory_usage = 0
	celery_process_info = []
	for process in celery_processes:
		mem_info = process.memory_info()
		amount = mem_info.rss / (1024 * 1024)  # Convert to MB
		celery_process_info.append(round(amount, 2))
		celery_memory_usage += amount

	cpu_usage = psutil.cpu_percent()
	total_system_memory = psutil.virtual_memory().total / (1024 * 1024)  # Convert to MB

	top_processes = []
	for proc in psutil.process_iter():
		try:
			process_memory = proc.memory_info().rss / (1024 * 1024)
			top_processes.append({"name": proc.name(), "memory": round(process_memory, 2)})
		except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
			pass

	top_processes.sort(key=lambda x: x["memory"], reverse=True)
	top_processes = top_processes[:10]  # Limit to top 10 processes

	available_memory = psutil.virtual_memory().available / (1024 * 1024)  # Convert to MB

	# Get the top memory-consuming Django views/functions
	tracemalloc.start()
	top_views = tracemalloc.take_snapshot().statistics('lineno')[:5]

	# Get memory usage for each Celery worker and task
	celery_worker_info = []
	for worker in celery_processes:
		try:
			worker_memory = worker.memory_info().rss / (1024 * 1024)
			task_name = 'unknown'
			try:
				task_name = worker.cmdline()[2]
			except IndexError:
				pass
			celery_worker_info.append({'name': task_name, 'memory': round(worker_memory, 2)})
		except psutil.NoSuchProcess:
			celery_worker_info.append({'name': 'Terminated Worker', 'memory': 0})

	# Get memory usage of Python processes
	python_processes = []
	for proc in psutil.process_iter():
		try:
			if "python" in proc.name().lower():
				python_processes.append(proc)
		except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
			celery_worker_info.append({'name': 'Terminated Python Process', 'memory': 0})


	python_process_info = []
	for process in python_processes:
		try:
			mem_info = process.memory_info()
			amount = mem_info.rss / (1024 * 1024)  # Convert to MB
			python_process_info.append({"name": process.name(), "memory": round(amount, 2)})
		except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
			celery_worker_info.append({'name': 'Terminated Process', 'memory': 0})

	# Get the memory usage percentage
	memory_percent = psutil.virtual_memory().percent

	return JsonResponse({
		'memory_usage': round(total_memory_usage, 2),
		'celery': round(celery_memory_usage, 2),
		'celery_tasks': celery_process_info,
		'cpu_usage': round(cpu_usage, 2),
		'total_system_memory': round(total_system_memory, 2),
		'available_memory': round(available_memory, 2),
		'memory_percent': round(memory_percent, 2),
		'processes': top_processes,
		'top_views': [{'filename': s.traceback[0].filename, 'lineno': s.traceback[0].lineno, 'size': round(s.size / (1024 * 1024), 2)} for s in top_views],
		'celery_workers': celery_worker_info,
		'python_processes': python_process_info,
	})
