#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Project: Ubermag
Path:    include/Uberwidgets/user_interface/style.py

Description:
    Short description of what this (style.py) does.
    
Author:      Cameron Aidan McEleney < c.mceleney.1@research.gla.ac.uk >
Created:     25 Apr 2025
IDE:         PyCharm
Version:     0.1.0
"""

# Standard library imports
from ipywidgets import Layout

# Third-party imports

# Local application imports

__all__ = [
    "desc_style",
    "widget_width",
    "desc_style",
    "full_layout",
    "align_left",
]

# Constants
desc_width  = '180px'
widget_width= '400px'

desc_style = {'description_width': desc_width}
full_layout= Layout(width=widget_width)
align_left = Layout(
    display='flex', flex_flow='column',
    align_items='flex-start',
    padding='0px', border='1px solid #ddd',
)
