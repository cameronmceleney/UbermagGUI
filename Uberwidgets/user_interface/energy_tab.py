#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Project: Ubermag
Path:    include/Uberwidgets/user_interface/energy_tab.py

Description:
    Short description of what this (energy_tab.py) does.

Author:      Cameron Aidan McEleney < c.mceleney.1@research.gla.ac.uk >
Created:     25 Apr 2025
IDE:         PyCharm
Version:     0.1.0
"""
from importlib.metadata import metadata

# Standard library imports
from ipywidgets import Checkbox, HTML, Select, Stack, VBox, Accordion

# Third-party imports

# Local application imports
from ..metadata.enable_energy_terms import EnableEnergyTerms
from .style import full_layout, align_left
from Uberwidgets.metadata.descriptors import _dmi_desc

__all__ = ["make_energy_tab"]


def make_energy_tab(initial: EnableEnergyTerms):
    # 1) Core checkboxes
    flags = {}
    for name in ['anisotropy','demag','driving_zeeman','exchange','static_zeeman']:
        flags[name] = Checkbox(
            value=getattr(initial, name),
            description=EnableEnergyTerms.label(name)
        )

    dmi_keys = list(_dmi_desc._dmi_flags.keys())  # ['constant','dictionary','subregions']

    wg_enable_dmi = Checkbox(False, description='Enable DMI options')
    off = HTML("<i>DMI disabled</i>", layout=full_layout)
    wg_dmi_method = Select(
        options=dmi_keys,
        value=dmi_keys[0],
        description=EnableEnergyTerms.label('dmi'),
        layout=full_layout
    )

    stack = Stack([off, wg_dmi_method], selected_index=0)
    wg_enable_dmi.observe(
        lambda ch: setattr(stack, 'selected_index', 1 if ch['new'] else 0),
        names='value'
    )

    box = VBox(
        [*flags.values(), wg_enable_dmi, stack],
        layout=align_left
    )
    acc = Accordion([box])
    acc.set_title(0, 'Energy term flags')
    acc.selected_index = 0

    widgets_map = {**flags,
                   'enable_dmi': wg_enable_dmi,
                   'dmi_method': wg_dmi_method}

    return acc, widgets_map
