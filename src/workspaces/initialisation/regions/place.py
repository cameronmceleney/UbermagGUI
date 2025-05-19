#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Project: UbermagGUI
Path:    src/workspaces/initialisation/regions/place.py

PlaceRegionInModel:
    name + pmin/pmax + Place button to add a subregion to the model.

This panel gathers the name and coordinates of a new subregion, informs
ControlsPanel of that addition (in SI), and triggers a redraw of ViewportArea.
"""
# Standard library imports
import logging
import ipywidgets as widgets
from ipywidgets import Layout

# Third-party imports
import discretisedfield as df

# Local application imports
from src.config.type_aliases import UNIT_FACTORS
from src.config.dataclass_containers import _CoreProperties
from src.helper_functions import build_widget_input_values_xyz_tuple

__all__ = ["PlaceRegion"]

logger = logging.getLogger(__name__)


class PlaceRegion:
    def __init__(self):
        # callbacks to ControlsPanel
        self._state_cb = None

        # Build-time attributes
        self._sys_props = None

        # Widgets (will be re-created each build)
        # widgets will be set in build()
        self.text_name = None
        self.pmin_x = self.pmin_y = self.pmin_z = None
        self.pmax_x = self.pmax_y = self.pmax_z = None
        self.btn_place = None

    def set_state_callback(self, cb):
        """Register the GeometryController._on_domain callback."""
        self._state_cb = cb

        if self._state_cb and getattr(self, "btn_place", None):
            self.btn_place.on_click(self._on_place)

    def build(self, context: _CoreProperties) -> widgets.VBox:
        """
        Build and return the UI for placing a subregion.
        Capture controls_panel for dims/units lookups.
        """
        self._sys_props = context

        place_panel = widgets.VBox(
            layout=Layout(
                overflow='auto',
                padding='4px',

            )
        )
        panel_children = []

        # Explanation HTML
        # 1) Explanation HTML about purpose of panel
        html_explainer_region = widgets.HTML(
            value="Define a new region which can be positioned anywhere in the domain.",
            layout=widgets.Layout(
                width='auto',
            )
        )
        panel_children.append(html_explainer_region)

        html_region_name = widgets.HTML(
            value="New region",
        )
        self.text_name = widgets.Text(
            placeholder="name",
            layout=Layout(width='40%'),
        )
        hbox_region_name = widgets.HBox(
            children=[html_region_name, self.text_name],
            layout=Layout(
                width='auto',
                height='auto',
                align_items='center',
                align_content='center',
                justify_content='flex-end',
            )
        )
        panel_children.append(hbox_region_name)

        self._position_widgets(panel_children)

        # Place button (auto width) and center-justified
        self.btn_place = widgets.Button(
            description='Place region',
            layout=Layout(width='auto'),
            style={'button_width': 'auto'}
        )

        # always wire the click -> our handler; callback stored in self._state_cb
        self.btn_place.on_click(self._on_place)

        btn_box = widgets.HBox(
            [self.btn_place],
            layout=Layout(justify_content='center', width='100%')
        )
        panel_children.append(btn_box)

        place_panel.children = tuple(panel_children)
        return place_panel

    def _on_place(self, _):
        """When user clicks 'Place Region'—convert inputs to SI, register, redraw."""
        name = self.text_name.value.strip()

        pmin_raw = tuple(map(float, (self.pmin_x.value, self.pmin_y.value, self.pmin_z.value)))
        pmax_raw = tuple(map(float, (self.pmax_x.value, self.pmax_y.value, self.pmax_z.value)))

        logger.debug("PlaceRegion._on_place called; name=%r, pmin=%r, pmax=%r",
                     self.text_name, pmin_raw, pmax_raw)

        # Convert to SI using controls.units
        factor = UNIT_FACTORS.get(self._sys_props.units[0], 1.0)
        pmin_si = tuple(v * factor for v in pmin_raw)
        pmax_si = tuple(v * factor for v in pmax_raw)

        # Create the new Region (in SI units, tagged with user units)
        region = df.Region(
            p1=pmin_si, p2=pmax_si,
            dims=self._sys_props.dims,
            units=self._sys_props.units
        )

        # Hand off to WorkspaceController
        if self._state_cb:
            self._state_cb(name, region)

        logger.success("PlaceRegion._on_place: call complete.")

    def _position_widgets(self, panel_children):

        # Might copy & reference Ubermag's df.Region.pmin docstring in the future
        html_domain_explainer = widgets.HTMLMath(
            value="Define the two diagonally-opposite corners of the region:",
            layout=widgets.Layout(
                overflow_y="visible",
                align_content="stretch",
                justify_content="flex-start",)
        )
        panel_children.append(html_domain_explainer)

        # 2) pmin row
        hbox_pmin = build_widget_input_values_xyz_tuple(r"\(\mathbf{p}_1\)", default=(0, 0, 0))
        panel_children.append(hbox_pmin)
        self.pmin_x = hbox_pmin.children[1]
        self.pmin_y = hbox_pmin.children[2]
        self.pmin_z = hbox_pmin.children[3]

        # 3) pmax row
        hbox_pmax = build_widget_input_values_xyz_tuple(r"\(\mathbf{p}_2\)", default=(1, 1, 1))
        panel_children.append(hbox_pmax)
        self.pmax_x = hbox_pmax.children[1]
        self.pmax_y = hbox_pmax.children[2]
        self.pmax_z = hbox_pmax.children[3]

        html_units_explainer = widgets.HTMLMath(
            value=f"(Units: {self._sys_props.units[0]})",
            layout=widgets.Layout(
                width="auto",
                justify_content="flex-end",
            )
        )
        panel_children.append(html_units_explainer)
