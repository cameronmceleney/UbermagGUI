#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Project: UbermagGUI
Path:    src/workspaces/initialisation/panels/xyz_inputs.py

Description:
    Short description of what this (xyz_inputs.py) does.
    
Author:      Cameron Aidan McEleney < c.mceleney.1@research.gla.ac.uk >
Created:     20 May 2025
IDE:         PyCharm
Version:     0.1.0
"""

# Standard library imports
from dataclasses import dataclass, field
from typing import Optional, Union
import ipywidgets as widgets

# Third-party imports

# Local application imports

__all__ = [
    "ThreeCoordinateInputs"
]

_NumericProtocol = Union[widgets.FloatText, widgets.Text]


@dataclass
class ThreeCoordinateInputs:
    """
    Container for three coordinate input widgets (x, y, z).

    Provides helpers to read and write their numeric values.
    """
    x: Optional[_NumericProtocol]
    y: Optional[_NumericProtocol]
    z: Optional[_NumericProtocol]
    _hbox: Optional[widgets.HBox] = field(init=False, default=None)

    @property
    def hbox(self) -> widgets.HBox:
        """Container to embed into panels."""
        if self._hbox is None:
            # TODO. Implement logger.
            raise RuntimeError(
                "ThreeCoordinateInputs.hbox was never set—"
                "please construct via ThreeCoordinateInputs.from_defaults()"
            )
        return self._hbox

    @property
    def values(self) -> tuple[Optional[float], ...]:
        """
        Read the current values from all three widgets.

        Permit `None` entries in the tuple to allow for error checking within `controllers`.
        """
        values: list[Optional[float]] = []
        for v in (self.x, self.y, self.z):
            if v is None or v.value is None or v.value == "":
                # TODO. Insert proper debugging
                values.append(None)
            else:
                values.append(float(v.value))
        return tuple(values)

    @values.setter
    def values(self, values: tuple[float, float, float]) -> None:
        """
        Update the three widgets.
        """
        for widget, val in zip((self.x, self.y, self.z), values):
            if widget is not None:
                widget.value = val

    @classmethod
    def from_defaults(
            cls,
            label_tex: str,
            defaults: tuple[float, float, float]
    ) -> "ThreeCoordinateInputs":
        """
        Factory that builds three widgets and wraps them in an `iypywidget.HBox`.

        Particularly useful when constructing panels that require inputs for:
            - Cartesian coordinates;
            - cell sizes.
        """
        textbox_layout = widgets.Layout(
            flex='0 0 auto',
            width="3em",  # Internal default to ensure immutable consistency across all panels
        )

        text_widgets = []
        for val in defaults:
            text_widgets.append(widgets.FloatText(value=val, layout=textbox_layout))

        label = widgets.HTMLMath(label_tex, layout=widgets.Layout(flex="0 0 auto"))

        hbox = widgets.HBox(
            [label, *text_widgets],
            layout=widgets.Layout(align_items="center", justify_content="flex-end", gap="4px"),
        )

        inst = cls(*text_widgets)
        inst._hbox = hbox

        return inst
