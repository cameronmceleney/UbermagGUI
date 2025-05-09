#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Project: Ubermag
Path:    include/Uberwidgets/user_interface/material_tab.py

Description:
    Short description of what this (material_tab.py) does.
    
Author:      Cameron Aidan McEleney < c.mceleney.1@research.gla.ac.uk >
Created:     25 Apr 2025
IDE:         PyCharm
Version:     0.1.0
"""

# Standard library imports
from ipywidgets import FloatText, Accordion, VBox

# Third-party imports

# Local application imports
from ..metadata.enable_simulation_params import EnableSimulationParameters
from .style import desc_style, full_layout, align_left

__all__ = ["make_material_tab"]


def make_material_tab(initial: EnableSimulationParameters):
    flags = {}
    wg_drive = FloatText(
        value=initial.driving_frequency,
        description='Drive freq (GHz):',
        style=desc_style, layout=full_layout
    )
    wg_sat = FloatText(
        value=initial.saturation_magnetisation,
        description='Saturation M (A/m):',
        style=desc_style, layout=full_layout
    )

    flags['driving_frequency'] = wg_drive
    flags['saturation_magnetisation'] = wg_sat

    box = VBox(
        [*flags.values()],
        layout=align_left
    )
    acc = Accordion([box])
    acc.set_title(0, 'Material properties')
    acc.selected_index = 0

    widgets_map = {**flags}

    return acc, widgets_map
