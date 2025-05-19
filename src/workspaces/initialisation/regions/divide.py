#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Project: UbermagGUI
Path:    src/workspaces/initialisation/regions/divide.py

Description:
        DividePanel: base dropdown, scale, Name, Divide button.

Warning:
    Currently not working/implemented!
    
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
import discretisedfield as df

# Local application imports


__all__ = ["DivideRegion"]


class DivideRegion:
    def __init__(self):
        # callback to WorkspaceController.add_subregion(name, region)
        self._state_cb = None
        # stash controller so we can read .subregions, .dims, .units
        self._controls = None

        # Widgets
        self.dd_base = widgets.Dropdown(options=[], description="Base:")
        self.dd_axes = widgets.HBox([
            widgets.Checkbox(value=True, description="X-axis"),
            widgets.Checkbox(value=False, description="Y-axis"),
            widgets.Checkbox(value=False, description="Z-axis"),
        ])
        self.text_name = widgets.Text(description="Name:")
        self.float_scale = widgets.FloatText(1.0, description="Scale:")
        self.btn_divide = widgets.Button(description="Divide", layout=Layout(width="auto"))

    def set_state_callback(self, cb):
        """Register WorkspaceController.add_subregion."""
        self._state_cb = cb
        # wire our button
        self.btn_divide.on_click(self._on_divide)

    def build(self, controller) -> widgets.VBox:
        """
        Build the UI, refresh dropdown of bases, and return as a VBox.
        """
        self._controls = controller
        # refresh list of base regions
        bases = ["main"] + list(controller.subregions.keys())
        self.dd_base.options = bases

        return widgets.VBox(
            [
                self.dd_base,
                self.dd_axes,
                self.text_name,
                self.float_scale,
                self.btn_divide,
            ],
            layout=Layout(overflow="auto", padding="4px"),
        )

    def _on_divide(self, _):
        """
        When user clicks 'Divide':
          1) read base region, axes, scale
          2) slice & subdivide region
          3) call state_cb(name, new_region)
        """
        base_key = self.dd_base.value
        name = self.text_name.value.strip()
        if not name:
            self.btn_divide.button_style = "danger"
            return

        # determine axes to divide along
        axes = []
        for idx, cb in enumerate(self.dd_axes.children):
            if cb.value:
                axes.append(self._controls.dims[idx])
        scale = self.float_scale.value

        # look up the base region
        parent = (
            self._controls.main_region
            if base_key == "main"
            else self._controls.subregions.get(base_key)
        )
        if parent is None:
            self.btn_divide.button_style = "danger"
            return

        # **Here you would implement your actual divide logic**—
        # for now, we just clone the parent region scaled along chosen axes.
        p1, p2 = parent.pmin, parent.pmax
        # naive: shrink p2 by scale along each selected axis index
        new_p1 = list(p1); new_p2 = list(p2)
        for ax in axes:
            i = self._controls.dims.index(ax)
            length = (p2[i] - p1[i]) * scale
            new_p2[i] = p1[i] + length

        region = df.Region(
            p1=tuple(new_p1),
            p2=tuple(new_p2),
            dims=self._controls.dims,
            units=self._controls.units,
        )

        # notify upper‐level controller
        if self._state_cb:
            self._state_cb(name, region)