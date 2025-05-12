#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Project: UbermagGUI
Path:    src/status_bars/status_bars.py

Description:
        Defines the footer bar with the Instantiate button.
    
Author:      Cameron Aidan McEleney < c.mceleney.1@research.gla.ac.uk >
Created:     29 Apr 2025
IDE:         PyCharm
Version:     0.1.0
"""

# Standard library imports

# Third-party imports
import ipywidgets as widgets
from ipywidgets import Layout

# Local application imports

__all__ = ["StatusBar"]


class StatusBar:
    def __init__(self):
        self.btn_instant = widgets.Button(
            description='Instantiate', layout=Layout(width='auto')
        )
        self.container = widgets.HBox([self.btn_instant], layout=Layout(justify_content='flex-end'))

    def build(self):
        return self.container