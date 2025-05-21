#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Project: UbermagGUI
Path:    src/workspaces/initialisation/meshes/create_mesh.py

Description:

    CreateMesh: define your df.Mesh for the micromagnetic System.

    Inherits layout + callback wiring from _PanelBase. Its typical caller will be
    `InitialisationController`.
    
Author:      Cameron Aidan McEleney < c.mceleney.1@research.gla.ac.uk >
Created:     04 May 2025
IDE:         PyCharm
Version:     0.1.0
"""

# Standard library imports
import ipywidgets as widgets
import logging
from typing import Any, Sequence

# Third-party imports
import discretisedfield as df

# Local application imports
from src.workspaces.initialisation.panels import _PanelBase

__all__ = ["CreateMesh"]

logger = logging.getLogger(__name__)


class CreateMesh(_PanelBase):
    """
    Panel to build a mesh from an existing Region.

    Attributes
    ----------
    dd_base_region : widgets.Dropdown
        Select which region to mesh.
    dd_bc_type : widgets.Dropdown
        Boundary‐condition type.
    ckk_bc_x, ckk_bc_y, ckk_bc_z : widgets.Checkbox
        Choose periodic axes for "periodic" BC.
    btn_build_mesh : widgets.Button
        Trigger mesh construction.
    """
    dd_base_region: widgets.Dropdown
    dd_bc_type: widgets.Dropdown
    ckk_bc_x: widgets.Checkbox
    ckk_bc_y: widgets.Checkbox
    ckk_bc_z: widgets.Checkbox
    btn_build_mesh: widgets.Button

    def __init__(self):
        super().__init__()

    def _assemble_panel(self, children: list[widgets.Widget]) -> None:
        # Title + explainer
        children.append(widgets.HTML("<b>Generate mesh.</b>"))

        children.append(
            widgets.HTML(value="Discretise a base region using a regular finite-difference method.",
                         layout=widgets.Layout(width="auto")
                         )
        )

        # 1) base-region selector
        children.append(self._make_base_region_row())

        # 2) boundary conditions block
        self._build_boundary_conditions(children)

        # 3) build-mesh button
        children.append(self._make_button_row())

    def _make_base_region_row(self) -> widgets.HBox:
        """Construct the base-region dropdown row."""
        label = widgets.HTML("Base region for mesh", layout=widgets.Layout(width="auto"))

        self.dd_base_region = widgets.Dropdown(layout=widgets.Layout(width="40%"))
        hbox = widgets.HBox(
            [label, self.dd_base_region],
            layout=widgets.Layout(
                align_items="center",
                justify_content="flex-end",
                gap="4px"
            )
        )

        return hbox

    def _make_button_row(self) -> widgets.HBox:
        """Construct the Build Mesh button row."""
        self.btn_build_mesh = widgets.Button(
            description="Build Mesh",
            button_style="primary",
            layout=widgets.Layout(width="auto")
        )

        # wire click if callback already set
        if self._ctrl_cb:
            self.btn_build_mesh.on_click(self._on_create_mesh)

        hbox = widgets.HBox(
            [self.btn_build_mesh],
            layout=widgets.Layout(justify_content="center", width="100%")
        )

        return hbox

    def _on_create_mesh(self, _: Any) -> None:
        """Build df.Mesh and fire the callback."""
        key = self.dd_base_region.value
        bc = self._on_dropdown_bc()
        base_region = self._sys_props.regions.get(key)
        if base_region is None:
            self.btn_build_mesh.button_style = "danger"
            return

        try:
            mesh = df.Mesh(region=base_region, cell=self._sys_props.cell, bc=bc)
        except Exception as e:
            logger.error("Mesh creation failed: %s", e, exc_info=True)
            self.btn_build_mesh.button_style = "danger"
            return

        self.btn_build_mesh.button_style = "success"

        # Controller callback to update _CoreProperties
        if self._ctrl_cb:
            self._ctrl_cb(mesh)

        # Repopulate base regions in case new ones appeared
        self.refresh()

    def _build_boundary_conditions(self, children: list[widgets.Widget]) -> None:
        """
        Append boundary‐condition selector + context‐sensitive options.
        """

        children.append(widgets.HTMLMath(
            value=(
                "Boundary conditions should be specified. "
                "The default setting is Open."
            ),
            layout=widgets.Layout(width="auto")
        ))

        # Boundary condition (BC) options must be taken directly from ubermag
        # TODO. Link `bc_opts` with `df.Mesh.bc.setter` to automatically import valid options
        bc_opts = [
            ("Open", "open"),
            ("Periodic", "periodic"),
            ("Neumann", "neumann"),
            ("Dirichlet", "dirichlet"),
        ]
        max_len = max(len(lbl) for lbl, _ in bc_opts)
        dd_w = f"{max_len*1.5+2}ch"
        self.dd_bc_type = widgets.Dropdown(
            options=bc_opts,
            value="open",
            layout=widgets.Layout(width=dd_w)
        )

        # per-axis checkboxes. `style` required to keep widget dimensions small
        self.ckk_bc_x = widgets.Checkbox(description="x", value=False,
                                         style={'description_width': '2rem'},
                                         layout=widgets.Layout(width="auto")
                                         )
        self.ckk_bc_y = widgets.Checkbox(description="y", value=False,
                                         style={'description_width': '2rem'},
                                         layout=widgets.Layout(width="auto")
                                         )
        self.ckk_bc_z = widgets.Checkbox(description="z", value=False,
                                         style={'description_width': '2rem'},
                                         layout=widgets.Layout(width="auto")
                                         )

        # stacks of extra options
        hbox_none = widgets.HBox([widgets.HTML("<b>None</b>")],
                                 layout=widgets.Layout(align_items="center", gap="4px"))
        hbox_periodic = widgets.HBox(
            [self.ckk_bc_x, self.ckk_bc_y, self.ckk_bc_z],
            layout=widgets.Layout(align_items="center", justify_content='center', gap="4px")
        )
        hbox_neu = widgets.HBox([widgets.HTML("<b>None</b>")],
                                layout=widgets.Layout(align_items="center", gap="4px"))
        hbox_dir = widgets.HBox([widgets.HTML("<b>None</b>")],
                                layout=widgets.Layout(align_items="center", gap="4px"))

        stack = widgets.Stack(
            children=[hbox_none, hbox_periodic, hbox_neu, hbox_dir],
            selected_index=0,
            layout=widgets.Layout(width="auto")
        )
        widgets.jslink((self.dd_bc_type, "index"), (stack, "selected_index"))

        # group dropdown + stack
        children.append(widgets.VBox(
            [self.dd_bc_type, stack],
            layout=widgets.Layout(align_items="center", gap="4px")
        ))

    def _on_dropdown_bc(self) -> str:
        """Translate widget states into the df.Mesh bc string."""
        mode = self.dd_bc_type.value
        match mode:
            case "open":
                return ""

            case "periodic":
                # Defaults to open if no checkboxes were selected.
                bc = ''
                if self.ckk_bc_x.value: bc += 'x'
                if self.ckk_bc_y.value: bc += 'y'
                if self.ckk_bc_z.value: bc += 'z'
                return bc

            case "neumann":
                return mode

            case "dirichlet":
                return mode

        raise NotImplementedError(f"BC mode {mode!r}")

    def refresh(self, *_) -> None:
        """
        Refresh the “base region” dropdown and enable/disable the build button
        based entirely on self._sys_props.regions (and self._sys_props.main_region).

        Called whenever regions are added/removed upstream.
        """
        regions_list = list(self._sys_props.regions.keys())
        logger.debug("CreateMesh.refresh: computed bases=%r", regions_list)

        self.dd_base_region.options = regions_list
        self.btn_build_mesh.disabled = not bool(regions_list)

        # pick first if current no longer valid
        if regions_list and self.dd_base_region.value not in regions_list:
            self.dd_base_region.value = regions_list[0]
        # clear any “danger” style if previously failed
        if not self.btn_build_mesh.disabled:
            self.btn_build_mesh.button_style = ""
