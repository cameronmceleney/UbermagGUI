#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Project: Ubermag
Path:    include/Uberwidgets/user_interface/dynamic_tab.py

Description:
    Short description of what this (dynamic_tab.py) does.
    
Author:      Cameron Aidan McEleney < c.mceleney.1@research.gla.ac.uk >
Created:     25 Apr 2025
IDE:         PyCharm
Version:     0.1.0
"""

# Standard library imports
from ipywidgets import Dropdown, Stack, Button, VBox, Accordion, HTML, IntText, FloatText

# Third-party imports

# Local application imports
from ..metadata.enable_simulation_params import EnableSimulationParameters
from .style import desc_style, full_layout, align_left


__all__ = ["make_dynamic_tab"]


__all__ = ["make_dynamic_tab"]


def make_dynamic_tab(initial: EnableSimulationParameters):
    # 1) pick only the public fields
    public_fields = [
        name for name in initial.__dataclass_fields__.keys()
        if not name.startswith('_')
           and name != '__dataclass_fields__'
    ]

    # 2) create a widget for each field
    param_widgets: dict[str, FloatText | IntText] = {}
    for name in public_fields:
        default = getattr(initial, name)
        label   = EnableSimulationParameters.label(name)
        if isinstance(default, float):
            w = FloatText(
                value=default,
                description=label,
                style=desc_style, layout=full_layout
            )
        else:
            w = IntText(
                value=default,
                description=label,
                style=desc_style, layout=full_layout
            )
        param_widgets[name] = w

    # 3) dropdown to pick which one to show
    dropdown = Dropdown(
        options=public_fields,
        value=public_fields[0],
        description='Adjust param:',
        style=desc_style, layout=full_layout
    )

    # 4) stack of all those widgets
    stack = Stack(
        [param_widgets[name] for name in public_fields],
        selected_index=0
    )
    dropdown.observe(
        lambda change: setattr(
            stack, 'selected_index',
            public_fields.index(change['new'])
        ),
        names='value'
    )

    # 5) Add‐override button & display
    override_btn = Button(description='Add override',
                          button_style='info',
                          layout=full_layout)
    override_box = HTML()
    overrides: dict[str, float | int] = {}

    def _on_override(_):
        key = dropdown.value
        overrides[key] = param_widgets[key].value
        override_box.value = '<br>'.join(
            f"<b>{k}</b> = {v!r}" for k, v in overrides.items()
        )

    override_btn.on_click(_on_override)

    # 6) assemble
    container = VBox(
        [dropdown, stack, override_btn, override_box],
        layout=align_left
    )
    acc = Accordion([container])
    acc.set_title(0, 'Advanced')
    # acc.selected_index = 0

    # 7) widget_map includes all param widgets *and* the overrides dict
    widget_map: dict[str, object] = {
        **param_widgets,
        'dropdown': dropdown,
        'overrides': overrides
    }

    return acc, widget_map
