#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Project: UbermagGUI
Path:    src/workspaces/initialisation/regions/place.py

PlaceRegion:
    UI to set up a new subregion by specifying a name, pmin/pmax,
    then handing it back to the WorkspaceController.
"""
# Standard library imports
import logging
import ipywidgets as widgets
from ipywidgets import Layout

# Third-party imports
import discretisedfield as df

# Local application imports
from src.config.type_aliases import UNIT_FACTORS
from src.workspaces.initialisation.panels import _PanelBase, ThreeCoordinateInputs

__all__ = ["PlaceRegion"]

logger = logging.getLogger(__name__)


class PlaceRegion(_PanelBase):
    """
    PlaceRegion panel:

    Attributes
    ----------
    new_region : widgets.Text
        Text input for the new region's name.

    pmin : ThreeCoordinateInputs
        Three FloatText inputs for the minimum corner.

    pmax : ThreeCoordinateInputs
        Three FloatText inputs for the maximum corner.

    btn_place : widgets.Button
        Button to commit the new region.
    """
    new_region: widgets.Text
    pmin: ThreeCoordinateInputs
    pmax: ThreeCoordinateInputs
    btn_place: widgets.Button

    def __init__(self):
        super().__init__()

    def _assemble_panel(self, children: list[widgets.Widget]) -> None:

        children.append(widgets.HTML("<b>Define region.</b>"))

        children.append(widgets.HTML(
            value="Define a new region which can be positioned anywhere in the domain.",
            layout=Layout(width="auto")
        ))

        children.append(self._make_name_row())

        children.extend(self._make_coordinate_rows())

        children.append(self._make_place_button())

    def _make_name_row(self) -> widgets.HBox:
        label = widgets.HTML(value="New region")

        self.new_region = widgets.Text(
            placeholder="name",
            layout=Layout(width="40%")
        )

        hbox = widgets.HBox(
            [label, self.new_region],
            layout=Layout(
                align_items="center",
                justify_content="flex-end",
                gap="4px"
            )
        )

        return hbox

    def _make_coordinate_rows(self) -> list[widgets.Widget]:

        out: list[widgets.Widget] = []

        out.append(
            widgets.HTML(
                value="Define the two diagonally-opposite corners of the region:",
                layout=Layout(overflow_y="visible",
                              align_content="stretch",
                              justify_content="flex-start")
            )
        )

        self.pmin = ThreeCoordinateInputs.from_defaults(r"\(\mathbf{p}_1\)", (0, 0, 0))
        out.append(self.pmin.hbox)

        self.pmax = ThreeCoordinateInputs.from_defaults(r"\(\mathbf{p}_2\)", (1, 1, 1))
        out.append(self.pmax.hbox)

        out.append(
            widgets.HTMLMath(value=f"(Units: {self._sys_props.units[0]})",
                             layout=Layout(justify_content="flex-end")
                             )
        )

        return out

    def _make_place_button(self) -> widgets.HBox:
        self.btn_place = widgets.Button(
            description="Place region",
            layout=Layout(width="auto"),
            button_style='',  # default to Grey
            style={"button_width": "auto"}
        )
        # wire it now that btn_place exists
        if self._ctrl_cb:
            self.btn_place.on_click(self._on_place)

        hbox = widgets.HBox(
            [self.btn_place],
            layout=Layout(justify_content="center", width="100%")
        )

        return hbox

    def _on_place(self, _):
        """When the user clicks 'Place Region'—convert inputs to SI, register, redraw."""
        name = self.new_region.value.strip()

        if not name:
            self.btn_place.button_style = "danger"
            logger.error("PlaceRegion._on_place: no name provided")
            return

        logger.debug("PlaceRegion._on_place called; name=%r, pmin=%r, pmax=%r",
                     self.new_region, self.pmin.values, self.pmax.values)

        # Convert to SI using controls.units
        factor = UNIT_FACTORS.get(self._sys_props.units[0], 1.0)
        pmin_si = tuple(v * factor for v in self.pmin.values)
        pmax_si = tuple(v * factor for v in self.pmax.values)

        # Create the new Region (in SI units, tagged with user units)
        region = df.Region(
            p1=pmin_si, p2=pmax_si,
            dims=self._sys_props.dims,
            units=self._sys_props.units
        )

        # Hand off to WorkspaceController
        if self._ctrl_cb:
            self._ctrl_cb(name, region)

        logger.success("PlaceRegion: placed region %r %r", name, region)

    def refresh(self, bases: list) -> None:
        """Empty"""
        pass