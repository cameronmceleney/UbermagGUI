#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Project: UbermagGUI
Path:    src/workspaces/initialisation/regions/append.py

AppendRegionUsingBase:
    Extrude a new subregion off a base region (main or existing).
    Now refactored to use _PanelBase, ThreeCoordinateInputs, and region_utils.
"""
import logging
import ipywidgets as widgets
from ipywidgets import Layout
from typing import List, Any

from src.workspaces.initialisation.panels.base import _PanelBase
from src.workspaces.initialisation.panels.xyz_inputs import ThreeCoordinateInputs
from src.workspaces.initialisation.panels.region_utils import (
    create_scaled_region_from_base_region,
)

logger = logging.getLogger(__name__)


def _labeled_row(label: str, widget: widgets.Widget) -> widgets.HBox:
    """Small helper: puts a text label and a widget into a right‐justified row."""
    return widgets.HBox(
        [widgets.HTML(value=f"{label}"), widget],
        layout=Layout(
            align_items="center",
            justify_content="flex-end",
            gap="4px",
        ),
    )


class AppendRegionUsingBase(_PanelBase):

    def __init__(self):
        super().__init__()
        # these will be set in _assemble_panel
        self.text_name: widgets.Text
        self.dd_base: widgets.Dropdown
        self.tb_axis: widgets.ToggleButtons
        self.tb_side: widgets.ToggleButtons
        self.dd_scale_mode: widgets.Dropdown
        self.ftext_scale_amount: widgets.FloatText
        self.btn_append: widgets.Button

    def _assemble_panel(self, children: List[widgets.Widget]) -> None:
        # 1) Explainer
        children.append(widgets.HTML("<b>Append a new subregion</b>"))
        children.append(widgets.HTML(
            "Generate a new region by appending to an existing one."
        ))

        # 2) Region name
        self.text_name = widgets.Text(
            placeholder="name", layout=Layout(width="40%")
        )
        children.append(_labeled_row("New region", self.text_name))

        # 3) Base‐region dropdown
        self.dd_base = widgets.Dropdown(
            options=list(self._props.regions.keys()),
            layout=Layout(width="40%")
        )
        children.append(_labeled_row("Base region", self.dd_base))

        # 4) Orientation: axis + side
        children.append(widgets.HTML("Choose orientation:"))
        self.tb_axis = widgets.ToggleButtons(
            options=[("x","x"),("y","y"),("z","z")],
            style={"button_width":"auto"}
        )
        children.append(_labeled_row("Axis", self.tb_axis))

        self.tb_side = widgets.ToggleButtons(
            options=[("+ve","max"),("-ve","min")],
            style={"button_width":"auto"}
        )
        children.append(_labeled_row("Face", self.tb_side))

        # 5) Scaling controls
        children.extend(self._make_scaling_controls())

        # 6) Append button
        self.btn_append = widgets.Button(
            description="Append region",
            layout=Layout(width="auto")
        )
        self.btn_append.on_click(self._on_append)
        children.append(
            widgets.HBox([self.btn_append], layout=Layout(justify_content="center"))
        )

    def _make_scaling_controls(self) -> List[widgets.Widget]:
        out: List[widgets.Widget] = []
        out.append(widgets.HTML("Define how large the slab should be:"))

        # scale‐mode dropdown
        self.dd_scale_mode = widgets.Dropdown(
            options=[("Relative","relative"),("Absolute","absolute")],
            value="relative",
            layout=Layout(width="8ch")
        )
        out.append(_labeled_row("Mode", self.dd_scale_mode))

        # single FloatText for the amount
        self.ftext_scale_amount = widgets.FloatText(
            value=1.0, placeholder="cells or units",
            layout=Layout(width="4rem")
        )
        out.append(_labeled_row("Amount", self.ftext_scale_amount))
        return out

    def _on_append(self, _btn) -> None:
        """Gather inputs, build the new Region, and call back into the workspace."""
        name = self.text_name.value.strip()
        if not name:
            self.btn_append.button_style = "danger"
            logger.error("Region name missing")
            return

        # lookup parent Region
        key = self.dd_base.value
        parent = (
            self._props.main_region
            if key == "main" else
            self._props.regions.get(key)
        )
        if parent is None:
            self.btn_append.button_style = "danger"
            logger.error("No parent region found")
            return

        # compute new Region
        new_region = create_scaled_region_from_base_region(
            base_region=parent,
            scale_amount=self.ftext_scale_amount.value,
            cellsize=self._props.cell,
            reference_side=self.tb_side.value,
            scale_along_axis=self.tb_axis.value,
            scale_is_absolute=(self.dd_scale_mode.value == "absolute"),
        )

        # state‐callback into WorkspaceController
        if self._ctrl_cb:
            self._ctrl_cb(name, new_region)

    def refresh(self, bases: List[Any] = None) -> None:
        """
        Called when geometry changes, so we can update our dropdown of base‐regions.
        """
        # repopulate options; keep current selection if still valid
        current = self.dd_base.value
        opts = list(self._props.regions.keys())
        self.dd_base.options = opts
        if current in opts:
            self.dd_base.value = current