#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Project: UbermagGUI
Path:    src/workspaces/initialisation/fields/initial_magnetisation.py

DefineSystemInitialMagnetisation:
    UI to set the system’s initial fields Field (system.m).

On “Define m₀” click it emits a df.Field through the registered callback.
    
Author:      Cameron Aidan McEleney < c.mceleney.1@research.gla.ac.uk >
Created:     05 May 2025
IDE:         PyCharm
Version:     0.1.0
"""

# Standard library imports
import ipywidgets as widgets
import logging

# Third-party imports
import discretisedfield as df

# Local application imports
from src.workspaces.initialisation.panels.xyz_inputs import ThreeCoordinateInputs

__all__ = ["DefineSystemInitialMagnetisation"]

logger = logging.getLogger(__name__)


class DefineSystemInitialMagnetisation:
    def __init__(self):
        # callback(mesh_field: df.Field) → builder.system.m = mesh_field
        self._state_cb = None
        self._sys_props = None

        # widgets
        self.dd_mesh = None
        self.init_mag = ThreeCoordinateInputs(None, None, None)
        self.sat_mag = None
        self.chk_mask = None
        self.btn_define = None

    def set_state_callback(self, cb):
        """Register callback to receive the new df.Field."""
        self._state_cb = cb

    def build(self, context) -> widgets.VBox:
        """
        Build the UI and wire all callbacks.
        """
        self._sys_props = context

        panel = widgets.VBox(
            layout=widgets.Layout(
                width='auto',
                height='auto',
                overflow="hidden",
                padding="4px"
            ),
        )
        children = []

        html_explainer = widgets.HTML("<b>Set mesh's initial fields state.</b>")
        children.append(html_explainer)

        # HTML + DropDown both required to inline DropDown with subsequent HTML widget
        html_base_mesh = widgets.HTML(
            "For a given base mesh",
            layout=widgets.Layout(flex='0 0 auto')
        )
        self.dd_mesh = widgets.Dropdown(layout=widgets.Layout(flex="0 0 30%"))

        hbox_base_mesh = widgets.HBox(
            children=[html_base_mesh, self.dd_mesh],
            layout=widgets.Layout(
                display='flex',
                width='100%',
                flex_flow='row wrap',
                word_break='break-all',
                align_items='center',
                gap='4px'
            )
        )
        children.append(hbox_base_mesh)

        self._build_init_mag_vals(children)

        # 4) Saturation fields
        children.append(
            widgets.HTML(value="which is scaled by the saturation fields ",)
        )

        self.sat_mag = widgets.FloatText(
            value=800000,  # Translates to 8e5 A/m which is appropriate for YIG
            description=r"$M_\text{s}$",
            style={
                # TODO. Tune these dimensions to be more consistent with other widgets
                'description_width': '3rem',
            },
            layout=widgets.Layout(
                width='50%',
                height='auto',
                align_self='flex-end',
            )
        )
        children.append(self.sat_mag)

        # TODO. Turn units information into tooltip for FloatText input of sat-mag
        html_sat_mag_units = widgets.HTML(
            value="(Units: A/m)",
            layout=widgets.Layout(
                width="auto",
                align_self="flex-end",
            )
        )
        children.append(html_sat_mag_units)

        children.append(widgets.HTML(
            value="You can use a mask to restrict magnetic behaviours to particular regions of the mesh. "
                  "<b>Warning:</b> "
                  "Currently, this flag overrides any inputs in Masking panel! ",
            )
        )

        self.chk_mask = widgets.Checkbox(
            value=False,
            description="Use mask",
            style={
                'description_width': '10ch',
                'button_width': 'auto'
            },
            layout=widgets.Layout(
                width="auto",
                justify_content='flex-end'
            )
        )
        children.append(self.chk_mask)

        self.btn_define = widgets.Button(
            description="Define 𝐦₀",  # Button only accepts Unicode
            button_style="primary",
            layout=widgets.Layout(
                width="auto",
                align_self='center',
                padding='4px'
            )
        )
        children.append(self.btn_define)
        self.btn_define.on_click(self._on_define)

        panel.children = tuple(children)

        self.refresh()
        return panel

    def refresh(self, *_):
        """If controls_panel.mesh changes, update the mesh dropdown."""
        # do nothing until build() has run and assigned self._controls & self.dd_mesh
        # TODO. Change method to use `_CoreProperties._add_mesh('main', mesh_obj)
        if self._sys_props is None or self.dd_mesh is None:
            logger.debug("DefineSystemInitialMagnetisation.refresh: Unable to update DropDown "
                         "as source are invalid/empty")
            return

        # TODO. Permit multiple meshes to be accepted as inputs
        opts = []
        if self._sys_props.main_mesh is not None:
            opts = [("main", "main")]
        logger.debug("DefineSystemInitialMagnetisation.refresh: mesh options %r", opts)
        self.dd_mesh.options = opts

        # default to first option if none selected
        if opts and self.dd_mesh.value not in {v for _, v in opts}:
            self.dd_mesh.value = opts[0][1]

    def _on_define(self, _):
        """Called when “Define m₀” is clicked."""

        mesh = self._sys_props.main_mesh if self.dd_mesh.value == "main" else None

        if mesh is None:
            logger.error("DefineSystemInitialMagnetisation: no mesh selected", exc_info=False)
            self.btn_define.button_style = "danger"
            return

        sat_mag = float(self.sat_mag.value)
        mask = bool(self.chk_mask.value)
        logger.debug("DefineSystemInitialMagnetisation._on_define: vec=%r, sat=%r, mask=%r",
                     self.init_mag.values, sat_mag, mask)

        try:
            field = df.Field(mesh=mesh, value=self.init_mag.values, norm=sat_mag, valid=mask, nvdim=3,)
        except Exception as e:
            logger.error("Failed to build initial Field: %s", e, exc_info=True)
            self.btn_define.button_style = "danger"
            return

        # give user feedback
        self.btn_define.button_style = "success"
        logger.success("DefineSystemInitialMagnetisation._on_define: Built initial Field %r", field)

        # hand the mesh off to ControlsPanel
        if self._state_cb:
            self._state_cb(field)

    def _build_init_mag_vals(self, panel_children):
        """
        Build widgets to receive the initial fields values.
        """
        html_init_mag_explainer = widgets.HTMLMath(
            value=", enter a vector to represent the normalised initial fields ",
            layout=widgets.Layout(
                overflow_y="visible",
                align_content="stretch",
                justify_content="flex-start",)
        )
        panel_children.append(html_init_mag_explainer)

        self.init_mag = ThreeCoordinateInputs.from_defaults(r"\(\mathbf{m}_{0}\)", (0, 0, 1))
        panel_children.append(self.init_mag.hbox)
