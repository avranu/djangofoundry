"""

Metadata:

File: urls.py
Project: Django Foundry
Created Date: 04 Apr 2023
Author: Jess Mann
Email: jess.a.mann@gmail.com

-----

Last Modified: Wed Apr 19 2023
Modified By: Jess Mann

-----

Copyright (c) 2023 Jess Mann
"""
# Generic imports
from __future__ import annotations

# Django imports
from django.urls import path

# App Imports
from djangofoundry.controllers.memory import MemoryMonitorView, memory_usage

app_name = 'django-foundry'

urlpatterns = [
        path('memory-monitor/', MemoryMonitorView.as_view(), name='memory_monitor'),
        path('memory-monitor/memory-usage/', memory_usage, name='memory_usage'),
]
