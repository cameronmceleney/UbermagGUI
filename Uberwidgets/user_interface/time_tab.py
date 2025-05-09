#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Project: Ubermag
Path:    include/Uberwidgets/user_interface/time_tab.py

Description:
    Short description of what this (time_tab.py) does.
    
Author:      Cameron Aidan McEleney < c.mceleney.1@research.gla.ac.uk >
Created:     25 Apr 2025
IDE:         PyCharm
Version:     0.1.0
"""

# Standard library imports
from ipywidgets import FloatText, Accordion, VBox, IntText

# Third-party imports

# Local application imports
from ..metadata.enable_simulation_params import EnableSimulationParameters
from .style import desc_style, full_layout, align_left

__all__ = ["make_time_tab"]


def make_time_tab(initial: EnableSimulationParameters):

    wg_stepsize = FloatText(
        value=initial.simulation_stepsize,
        description='Time step (ns):',
        style=desc_style, layout=full_layout
    )
    wg_subdivs = IntText(
        value=initial.num_subdivisions,
        description='Subdivisions:',
        style=desc_style, layout=full_layout
    )

    # Pack the accordion after setting all the widgets
    box = VBox([wg_stepsize, wg_subdivs], layout=align_left)
    acc = Accordion([box])
    acc.set_title(0, 'Time controls')
    acc.selected_index = 0

    # Expose the widgets in a map so we can actually access the set values!
    widget_map = {
        'simulation_stepsize': wg_stepsize,
        'num_subdivisions':    wg_subdivs
    }

    return acc, widget_map
