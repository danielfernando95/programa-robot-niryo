import os
import sys

sys.path.insert(0, os.path.abspath('..'))
sys.path.insert(0, os.path.abspath('../..'))  

# Activamos que incluya los TODO
todo_include_todos = True

# Project info
project = 'Program Robot Niryo'
copyright = '2026, Daniel Fernando Reina'
author = 'Daniel Fernando Reina'
release = '0.1'

# Extensiones necesarias
extensions = [
    'sphinx.ext.autodoc',
    'sphinx.ext.viewcode',
    'sphinx.ext.todo',
]

templates_path = ['_templates']
exclude_patterns = []

# Tema HTML (elige UNO)
html_theme = 'sphinx_rtd_theme'
# html_theme = 'alabaster'  # <- opcional alternativo

html_static_path = ['_static']

