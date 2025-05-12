#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Project: UbermagGUI
Path:    /setup.py

Description:
    Short description of what this (setup.py) does.
    
Author:      Cameron Aidan McEleney < c.mceleney.1@research.gla.ac.uk >
Created:     12 May 2025
IDE:         PyCharm
Version:     0.1.0
"""

# Standard library imports
from setuptools import setup, find_packages

# Third-party imports

# Local application imports

setup(
  name="UbermagGUI",
  version="0.1",
  package_dir={"": "src"},
  packages=find_packages(where="src"),
  entry_points={
    "console_scripts": [
      "uberdesigner = builder:main",
    ],
  },
)