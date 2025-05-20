#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Project: UbermagGUI
Path:    src/workspaces/initialisation/regions/append.py

AppendRegionToExisting:
    Extrude a new subregion off a base region (main or existing).
"""
# Standard library imports
import logging

import ipywidgets as widgets
from typing import List

# Third-party imports

# Local application imports
from src.config.type_aliases import _AXIS_INDICES
from src.workspaces.initialisation.panels.base import _PanelBase
from src.workspaces.initialisation.panels.xyz_inputs import ThreeCoordinateInputs
from src.workspaces.initialisation.panels.region_utils import create_scaled_region_from_base_region


__all__ = ["AppendRegionUsingBase"]

logger = logging.getLogger(__name__)


def _labeled_row(label: str, widget: widgets.Widget) -> widgets.HBox:
    """Small helper: puts a text label and a widget into a right‐justified row."""
    return widgets.HBox(
        [widgets.HTML(value=f"{label}"), widget],
        layout=widgets.Layout(
            align_items="center",
            justify_content="flex-end",
            gap="4px",
        ),
    )


class AppendRegionUsingBase(_PanelBase):
    """
    A panel that lets you append a new Region by extruding off an existing one.

    Attributes
    ----------
    new_region : widgets.Text
        A text input for the user to name the new region.

    select_base_region : widgets.Dropdown
        Dropdown of existing region names from which to append.

    select_axis : widgets.ToggleButtons
        Axis along which to extrude ('x', 'y', or 'z').

    select_base_face : widgets.ToggleButtons
        Whether to append on the ‘min’ or ‘max’ face.

    select_scaling_mode : widgets.Dropdown
        Toggle between 'relative' (in cells) or 'absolute' (in distance).

    scaling_amount : widgets.FloatText
        Amount to scale by (cells or absolute units).

    btn_append : widgets.Button
        Button to trigger append action.
    """
    # Placeholders for widgets.
    new_region: widgets.Text
    select_base_region: widgets.Dropdown
    select_axis: widgets.ToggleButtons
    select_base_face: widgets.ToggleButtons
    select_scaling_mode: widgets.Dropdown
    scaling_amount: widgets.FloatText
    btn_append: widgets.Button
    
    def __init__(self):
        super().__init__()

    def _assemble_panel(self, children: List[widgets.Widget]) -> None:
        
        # Explainer
        children.append(
            widgets.HTML("<b>Append a new subregion</b>")
        )
        children.append(
            widgets.HTML("Generate a new region by appending to an existing one.")
        )
        
        # Obtain name of base Region via DropDown - I think it's cleaner than MultipleSelect
        self.new_region = widgets.Text(
            placeholder="name", layout=widgets.Layout(width="40%")
        )
        children.append(
            _labeled_row("New region", self.new_region)
        )
        
        self.select_base_region = widgets.Dropdown(
            options=list(self._sys_props.regions.keys()),
            layout=widgets.Layout(width="40%")
        )
        children.append(
            _labeled_row("Base region", self.select_base_region)
        )
        
        # From base-region choose: axis, and axis direction, to append along
        children.append(
            widgets.HTML("To set the orientation of the generated region provide:",
                         layout=widgets.Layout(overflow_y="visible"))
        )
        
        self.select_axis = widgets.ToggleButtons(
            options=[("x", "x"), ("y", "y"), ("z", "z")],
            style={"button_width": "auto"}
        )
        children.append(
            _labeled_row("axis", self.select_axis)
        )

        self.select_base_face = widgets.ToggleButtons(
            options=[("+ve", "max"), ("-ve", "min")],
            style={"button_width": "auto"}
        )

        children.append(
            _labeled_row("direction", self.select_base_face)
        )
        
        # Scaling controls
        children.extend(self._make_scaling_controls())

        # Append button
        self.btn_append = widgets.Button(
            description="Append region",
            layout=widgets.Layout(width="auto"),
            style = {'button_width': 'auto'}
        )
        if self._ctrl_cb:
            self.btn_append.on_click(self._on_append)

        children.append(
            widgets.HBox([self.btn_append], layout=widgets.Layout(justify_content="center"))
        )
        
    def _make_scaling_controls(self) -> List[widgets.Widget]:
        
        out: List[widgets.Widget] = []
        # Explain to the user how the scaling works
        out.append(
            widgets.HTML("Define how the new region will be scaled:",
                         layout=widgets.Layout(overflow_y="visible", width="auto"))
        )

        # scale_mode_options must be compatible with region_utils/create_scaled_region_from_base_region.py
        scale_mode_options = [("Relative", "relative"), ("Absolute", "absolute")]
        max_label_length = max(len(label) for label, _ in scale_mode_options)
        self.select_scaling_mode = widgets.Dropdown(
            options=scale_mode_options,
            value="relative",
            layout=widgets.Layout(width=f"{max_label_length*1.5 + 2}ch")
        )

        # FloatText for the amount (shared by both modes)
        self.scaling_amount = widgets.FloatText(
            placeholder=1,
            layout=widgets.Layout(width="4rem")  # wide enough for “10000”
        )

        # Build the scaling_mode specific HBoxes that Stack will rotate through to inform user
        ax = _AXIS_INDICES[self.select_axis.value]

        scaling_info_rel = widgets.HTMLMath(
            value=(
                r"unit cells where<br>"
                rf"\(\Delta d_{{{self.select_axis.value}}} = {self._sys_props.cell[ax]}\)"
                f" {self._sys_props.units[ax]}"
            ),
            layout=widgets.Layout(width="auto", overflow_x='visible')
        )

        scaling_info_abs = widgets.HTMLMath(
            value=f"{self._sys_props.units[ax]}",
            layout=widgets.Layout(width="auto")
        )
        
        # Use same FloatText input in both to minimise number of input widget we're juggling
        hbox_rel = widgets.HBox(
            [self.scaling_amount, scaling_info_rel],
            layout=widgets.Layout(align_items="center", gap="4px")
        )
        hbox_abs = widgets.HBox(
            [self.scaling_amount, scaling_info_abs],
            layout=widgets.Layout(align_items="center", gap="4px")
        )

        # Stack and hook up the dropdown with the info boxes
        stack_length_scaling = widgets.Stack(
            children=[hbox_rel, hbox_abs],
            selected_index=0,
            layout=widgets.Layout(width="auto")
        )

        widgets.jslink((self.select_scaling_mode, 'index'), (stack_length_scaling, 'selected_index'))

        # 6) Finally put dropdown + stack side by side
        hbox_dropdown_plus_stack = widgets.HBox(
            [self.select_scaling_mode, stack_length_scaling],
            layout=widgets.Layout(width="auto", height="auto", align_items="center", gap="4px")
        )

        out.append(hbox_dropdown_plus_stack)
        
        return out

    def _on_append(self, _) -> None:
        """Gather inputs, build the new `df.Region`, and call back into the workspace via controller."""

        region_name = self.new_region.value.strip()
        if not region_name:
            self.btn_append.button_style = 'danger'
            logger.error('Region name either not provided, or None.', stack_info=True)
            return

        # Lookup base region
        base_key = self.select_base_region.value
        base_region = (
            self._sys_props.main_region 
            if base_key == "main" 
            else self._sys_props.regions.get(base_key))
        
        if base_region is None:
            self.btn_append.button_style = "danger"
            logger.error("No base region found")
            return

        # compute new Region (all SI internally)
        new_region = create_scaled_region_from_base_region(
            base_region=base_region,
            scale_amount=self.scaling_amount.value,
            cell=self._sys_props.cell,
            reference_side=self.select_base_face.value,
            scale_along_axis=self.select_axis.value,
            is_scale_absolute=(self.select_scaling_mode.value == "absolute")
        )

        # Callback into WorkspaceController
        if self._ctrl_cb:
            self._ctrl_cb(region_name, new_region)

    def refresh(self, bases: list) -> None:
        """
        Called when geometry changes, so we can update our dropdown of base‐regions.
        """
        current = self.select_base_region.value
        opts = list(self._sys_props.regions.keys())
        self.select_base_region.options = opts
        if current in opts:
            self.select_base_region.value = current