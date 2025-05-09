#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Project: Ubermag
Path:    include/Uberwidgets/region_designer_interface/workspace_modelling/feature_system_init/initial_magnetisation.py

DefineSystemInitialMagnetisation:
    UI to set the system’s initial magnetisation Field (system.m).

On “Define m₀” click it emits a df.Field through the registered callback.
    
Author:      Cameron Aidan McEleney < c.mceleney.1@research.gla.ac.uk >
Created:     05 May 2025
IDE:         PyCharm
Version:     0.1.0
"""

# Standard library imports
import ipywidgets as widgets
import logging
logger = logging.getLogger(__name__)

# Third-party imports
import discretisedfield as df

# Local application imports
from src.helper_functions import build_widget_input_values_xyz_tuple

__all__ = ["DefineSystemInitialMagnetisation"]


class DefineSystemInitialMagnetisation:
    def __init__(self):
        # callback(mesh_field: df.Field) → builder.system.m = mesh_field
        self._state_cb = None
        self._controls = None

        # widgets
        self.dd_mesh   = None
        self.init_mag_x     = None
        self.init_mag_y     = None
        self.init_mag_z     = None
        self.sat_mag    = None
        self.chk_mask  = None
        self.btn_define = None

    def set_state_callback(self, cb):
        """Register callback to receive the new df.Field."""
        self._state_cb = cb

    def build(self, controls_panel) -> widgets.VBox:
        """
        Build the UI:
          - choose from available meshes (today just “main”)
          - enter (mₓ, mᵧ, m𝓏)
          - enter saturation Mₛ
          - [mask toggle]  (no-op for now)
          - Define m₀ button
        """
        self._controls = controls_panel

        panel = widgets.VBox(
            layout=widgets.Layout(
                width='auto',
                height='auto',
                overflow="auto",
                padding="4px"
            ),
        )
        children = []

        # 1) Explanation
        html_explainer = widgets.HTML(
            "<b>Set mesh's initial magnetisation state.</b>"
        )
        children.append(html_explainer)

        # 2) Select base mesh
        # HTML + DropDown required to inline both with subsequent HTML widget
        html_base_mesh = widgets.HTML(
            "For a given base mesh",
            layout=widgets.Layout(flex='0 0 auto')
        )

        # TODO. Currently only accepting main_mesh; need to scale to all possible meshes
        if self._controls.mesh is None:
            mesh_options = []
        else:
            mesh_options = [("main mesh", "main")]

        # TODO. Currently only accepting main_mesh; need to scale to all possible meshes
        self.dd_mesh = widgets.Dropdown(
            options=mesh_options,
            layout=widgets.Layout(flex="0 0 30%")
        )

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

        # 3) Vector components
        self._build_init_mag_vals(children)

        # 4) Saturation magnetisation
        html_sat_mag = widgets.HTML(
            value="which is scaled by the saturation magnetisation ",
        )
        children.append(html_sat_mag)

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

        # 5) Mask toggle (placeholder; you’ll handle mask panels later)
        html_mesh_explainer = widgets.HTML(
            value="You can use a mask to restrict magnetic behaviours to particular regions of the mesh. "
                  "<b>Warning:</b> "
                  "Currently, this flag overrides any inputs in Masking panel! ",

        )
        children.append(html_mesh_explainer)
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

        # 6) Define button
        self.btn_define = widgets.Button(
            description="Define 𝐦₀",  # Button only accept Unicode here
            button_style="primary",  # TODO. Experiment if 'primary' or 'default' style is better for Buttons
            layout=widgets.Layout(
                width="auto",
                align_self='center',
                padding='4px'
            )
        )
        self.btn_define.on_click(self._on_define)

        children.append(self.btn_define)

        # 7) Assemble
        panel.children = tuple(children)
        return panel

    def refresh(self, *_):
        """If controls_panel.mesh changes, update the mesh dropdown."""
        # do nothing until build() has run and assigned self._controls & self.dd_mesh
        if not getattr(self, '_controls', None) or not hasattr(self, 'dd_mesh'):
            return

        opts = []
        if self._controls.mesh is not None:
            opts = [("Main mesh", "main")]
        self.dd_mesh.options = opts
        # default to first option if none selected
        if opts and self.dd_mesh.value not in {v for _, v in opts}:
            self.dd_mesh.value = opts[0][1]

    def _on_define(self, _):
        """Called when “Define m₀” is clicked."""
        # Validate
        if self._controls.mesh is None or self.dd_mesh.value is None:
            self.btn_define.button_style = "info"
            return

        vec = (
            float(self.init_mag_x.value),
            float(self.init_mag_y.value),
            float(self.init_mag_z.value)
        )
        sat_mag = float(self.sat_mag.value)

        logger.info("About to try building the field")
        try:
            field = df.Field(
                mesh=self._controls.mesh,
                value=vec,
                norm=sat_mag,
                valid=self.chk_mask.value,
                nvdim=3,
            )
        except Exception as e:
            # fail early, so we don’t break the widget
            logger.error("Failed to defining build m₀ field: %s", e, exc_info=True)
            self.btn_define.button_style = "danger"
            return

        # give user feedback
        self.btn_define.button_style = "success"
        logger.success(
            f"Built m₀ field. \n"
            f"Value: {field.value} \n"
            f"Valid: {field.valid} \n"
        )

        # hand the mesh off to ControlsPanel
        if self._state_cb:
            self._state_cb(field)

        self.refresh()

    def _build_init_mag_vals(self, panel_children):
        """
        Build widgets to receive the initial magnetisation values.
        """
        html_init_mag_explainer = widgets.HTMLMath(
            value=", enter a vector to represent the normalised initial magnetisation ",
            layout=widgets.Layout(
                overflow_y="visible",
                align_content="stretch",
                justify_content="flex-start",)
        )
        panel_children.append(html_init_mag_explainer)

        # 2) pmin row
        hbox_init_mag = build_widget_input_values_xyz_tuple(r"\(\mathbf{m}_{0}\)", default=(0, 0, 1))
        panel_children.append(hbox_init_mag)

        self.init_mag_x = hbox_init_mag.children[1]
        self.init_mag_y = hbox_init_mag.children[2]
        self.init_mag_z = hbox_init_mag.children[3]
