#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Project: UbermagGUI
Path:    src/workspaces/initialisation/fields/initial_magnetisation.py

SelectSubregionsInMesh:
    UI to include/exclude subregions in a given df.Mesh.

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
from src.workspaces.initialisation.panels import _PanelBase, ThreeCoordinateInputs

__all__ = ["DefineSystemInitialMagnetisation"]

logger = logging.getLogger(__name__)


class DefineSystemInitialMagnetisation(_PanelBase):
    """
    Panel to choose a base mesh, enter an initial magnetisation vector m₀,
    set a saturation Mₛ, optionally mask, and then emit a df.Field via callback.

    Attributes
    ----------
    dd_mesh : widgets.Dropdown
        Select target mesh.

    init_mag : ThreeCoordinateInputs
        Input initial (normalised) magnetisations for each unit cell.

    sat_mag : widgets.FloatText
        Saturation magnetisation.

    chk_mash : widgets.Checkbox
        Toggle to ``True`` unlocks an additional panel where the user can apply a mask.

    btn_define : widgets.Button
        Button to define the initiation magnetisation, and push this state to instanced
        `_CoreProperties.main_system.m0`.
    """
    dd_mesh: widgets.Dropdown
    init_mag: ThreeCoordinateInputs
    sat_mag: widgets.FloatText
    chk_mask: widgets.Checkbox
    btn_define: widgets.Button

    def __init__(self):
        super().__init__()

    def _assemble_panel(self, children: list[widgets.Widget]) -> None:
        # 1) Header
        children.append(widgets.HTML("<b>Set mesh’s initial fields state</b>"))

        # 2) Base‐mesh selector
        html_mesh = widgets.HTML(
            "For a given base mesh:",
            layout=widgets.Layout(flex="0 0 auto")
        )
        self.dd_mesh = widgets.Dropdown(layout=widgets.Layout(flex="0 0 30%"))
        html_and_dd = widgets.HBox(
            [html_mesh, self.dd_mesh],
            layout=widgets.Layout(
                display="flex",
                width="100%",
                flex_flow="row wrap",
                word_break="break-all",
                align_items="center",
                gap="4px",
            )
        )
        # Unsure if I need the following observe line of code
        self.dd_mesh.observe(lambda *_: self.refresh(), names="value")
        children.append(html_and_dd)

        self._make_init_mag_widgets(children)

        children.append(widgets.HTML(
            value="(Units: A/m)",
            layout=widgets.Layout(width="auto", align_self="flex-end")
        ))

        # 5) Mask checkbox
        children.append(widgets.HTML(
            value="You can restrict magnetic behaviours to certain regions using a mask. "
                  "<b>Warning:</b> "
                  "Currently, this flag overrides Mask panel inputs!",
            layout=widgets.Layout(width="auto")
        ))
        self.chk_mask = widgets.Checkbox(
            value=False,
            description="Use mask",
            style={"description_width": "10ch"},
            layout=widgets.Layout(justify_content="flex-end")
        )
        children.append(self.chk_mask)

        # 6) Define button
        self.btn_define = widgets.Button(
            description="Define 𝐦₀",
            button_style="primary",
            layout=widgets.Layout(align_self="center", padding="4px")
        )
        self.btn_define.on_click(self._on_define)

        children.append(self.btn_define)

    def refresh(self, *_) -> None:
        """
        Populate (or clear) the mesh‐dropdown based on whether a mesh exists.
        """
        if self._sys_props is None or self.dd_mesh is None:
            logger.debug(
                "DefineSystemInitialMagnetisation.refresh: "
                "missing dd_mesh or _sys_props, skipping"
            )
            return

        # rebuild the mesh list, human‐readable labels, disable if empty
        self._refresh_dropdown(
            self.dd_mesh,
            self._sys_props.meshes.keys(),
            labeler=str.title,              # e.g. "Main" instead of "main"
            default_first=True,             # pick the first if current invalid
            disable_widget=self.btn_define  # disable “Define m₀” if no meshes
        )

    def _make_init_mag_widgets(self, panel_children) -> None:
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

    def _on_define(self, _):
        """
        Gather inputs, build a df.Field, and emit it via the registered callback.
        """
        # 1) mesh lookup
        mesh = (self._sys_props.main_mesh
                if self.dd_mesh.value == "main"
                else None)
        if mesh is None:
            logger.error("No mesh selected")
            self.btn_define.button_style = "danger"
            return

        logger.debug("Init‐m₀: vec=%r, sat=%r, mask=%r",
                     self.init_mag.values,
                     self.sat_mag.value,
                     self.chk_mask.value)

        # Currently assumes we are always working in 3D space.
        try:
            field = df.Field(
                mesh=mesh,
                value=self.init_mag.values,
                norm=float(self.sat_mag.value),
                valid=bool(self.chk_mask.value),
                nvdim=3
            )
        except Exception as e:
            logger.error("Failed to build initial Field: %s", e, exc_info=True)
            self.btn_define.button_style = "danger"
            return

        # 4) feedback & callback
        self.btn_define.button_style = "success"
        logger.success("Built initial Field %r", field)
        if self._ctrl_cb:
            self._ctrl_cb(field)
