"""

Metadata:

File: python.py
Project: Django Foundry
Created Date: 11 Apr 2023
Author: Jess Mann
Email: jess.a.mann@gmail.com

-----

Last Modified: Tue Apr 11 2023
Modified By: Jess Mann

-----

Copyright (c) 2023 Jess Mann
"""
from django import template
from pygments import highlight
from pygments.formatters import HtmlFormatter
from pygments.lexers import PythonLexer
from pygments.styles import get_style_by_name

register = template.Library()

@register.filter
def python_code(value):
	style = get_style_by_name('monokai')
	formatter = HtmlFormatter(style=style)
	return highlight(value, PythonLexer(), formatter)
