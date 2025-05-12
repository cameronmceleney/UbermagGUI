#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Project: Ubermag
Path:    include/Uberwidgets/region_designer_interface/regions/divide.py

Description:
        DividePanel: base dropdown, scale, Name, Divide button.
    
Author:      Cameron Aidan McEleney < c.mceleney.1@research.gla.ac.uk >
Created:     29 Apr 2025
IDE:         PyCharm
Version:     0.1.0
"""

# Standard library imports
import ipywidgets as widgets
from ipywidgets import Layout
from IPython.display import display

# Third-party imports

# Local application imports

__all__ = ["DivideRegion"]


class DivideRegion:
    def __init__(self):
        self.dd_base = widgets.Dropdown(options=[], description='Base:')
        self.dd_axes = widgets.HBox([
            widgets.Checkbox(value=True, description='X-axis'),
            widgets.Checkbox(value=False, description='Y-axis'),
            widgets.Checkbox(value=False, description='Z-axis')
        ])
        self.text_name = widgets.Text(description='Name:')
        self.float_scale = widgets.FloatText(1.0, description='Scale:')
        self.btn_divide = widgets.Button(description='Divide', layout=Layout(width='auto'))
        self._plot_cb = None

    def set_plot_callback(self, func):
        self._plot_cb = func
        self.btn_divide.on_click(self._on_divide)

    def build(self, controller):
        box = widgets.VBox([self.dd_base, self.dd_axes, self.text_name, self.float_scale, self.btn_divide], layout=Layout(overflow='auto'))
        return box

    def refresh(self, bases):
        self.dd_base.options = bases

    def _on_divide(self, _):
        pass
