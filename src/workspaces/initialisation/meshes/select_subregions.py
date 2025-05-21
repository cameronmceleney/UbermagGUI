#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Project: UbermagGUI
Path:    src/workspaces/initialisation/meshes/select_subregions.py

SelectSubregionsInMesh:
    UI to include/exclude subregions in a given df.Mesh.
    
Author:      Cameron Aidan McEleney < c.mceleney.1@research.gla.ac.uk >
Created:     07 May 2025
IDE:         PyCharm
Version:     0.1.0
"""

# Standard library imports
import logging
import ipywidgets as widgets

# Third-party imports
import discretisedfield as df

# Local application imports
from src.workspaces.initialisation.panels import _PanelBase, ThreeCoordinateInputs


__all__ = ["SelectSubregionsInMesh"]


logger = logging.getLogger(__name__)


class SelectSubregionsInMesh(_PanelBase):
    """
    User can select to be included as subregions for a target mesh.

    The possible subregions come from a list of all regions saved to the `_CoreProperties.regions`
    instance.

    Attributes
    ----------
    dd_mesh : widgets.Dropdown
        Select which mesh to assign subregions.
    init_mag : ThreeCoordinateInputs
        Normalised magnetisation componets for each Cartesian axis.
    chk_mask : widgets.Checkbox
        Boolean check lets the user unlock an additional panel for defining masks.
    btn_define : widgets.Button
        Button to push selected subregions to instanced `_CoreProperties.main_mesh`.
    """
    dd_mesh: widgets.Dropdown
    init_mag: ThreeCoordinateInputs
    chk_mask: widgets.Checkbox
    btn_define: widgets.Button

    def __init__(self):
        # callback(mesh_field: df.Field) → builder.system.m = mesh_field
        super().__init__()

    def _assemble_panel(self, children: list[widgets.Widget]) -> None:

        children.append(
            widgets.HTML("<b>Include/Exclude Subregions</b>")
        )
        children.append(
            widgets.HTML("Select regions to include:")
        )

        # Select mesh
        html_mesh = widgets.HTML(
            "For a given base mesh:",
            layout=widgets.Layout(flex="0 0 auto")
        )
        self.dd_mesh = widgets.Dropdown(layout=widgets.Layout(flex="0 0 30%"))
        self.dd_mesh.observe(self._on_mesh_select, names="value")

        children.append(widgets.HBox(
            [html_mesh, self.dd_mesh],
            layout=widgets.Layout(
                display="flex",
                width="100%",
                flex_flow="row wrap",
                word_break="break-all",
                align_items="center",
                gap="4px",
            )
        ))

        # 3) Available ⇆ Included columns
        self._build_selection_boxes(children)

        # 4) Rebuild button
        self.btn_rebuild = widgets.Button(
            description="Rebuild Mesh",
            button_style="primary"
        )
        self.btn_rebuild.on_click(self._on_rebuild)

        children.append(widgets.HBox(
            [self.btn_rebuild],
            layout=widgets.Layout(justify_content="center")
        ))

    def refresh(self, *_) -> None:
        """
        Refresh the mesh dropdown + the Available/Includ ed lists based on current context.
        """
        if self._sys_props is None or self.dd_mesh is None:
            logger.debug(
                "SelectSubregionsInMesh.refresh: "
                "missing dd_mesh or _sys_props, skipping"
            )
            return

        has_mesh = bool(self._sys_props.main_mesh)

        # 1) rebuild the mesh dropdown
        self._refresh_dropdown(
            self.dd_mesh,
            self._sys_props.meshes.keys(),
            labeler=str.title,               # human‐readable
            default_first=True,              # pick first if old disappeared
            disable_widget=self.btn_rebuild  # disable “Rebuild” if no mesh
        )

        # 2) rebuild the two multi‐select lists
        all_names = set(self._sys_props.regions)
        chosen    = set(self._chosen)
        self.available.options = sorted(all_names - chosen)
        self.selected.options  = sorted(chosen & all_names)

    def _on_mesh_select(self, change):
        """Seed the chosen list from whatever the current mesh has."""
        new = change["new"]
        logger.debug("SelectSubregionsInMesh._on_mesh_select: %r", new)

        if new and self._sys_props.main_mesh:
            self._chosen = list(self._sys_props.main_mesh.subregions.keys())
        else:
            self._chosen = []
        self.refresh()

    def _build_selection_boxes(self, children: list[widgets.Widget]) -> None:
        """
        Append an explanatory text and an HBox of [ Available | → | Included ].
        """
        children.append(widgets.HTML(
            "Choose which regions to include as subregions of the mesh. "
            "Ensure that they are defined appropriately.",
            layout=widgets.Layout(flex="1 1 auto", min_width="0", overflow="visible")
        ))

        col_avail, self.available = self._make_column("Available", list(self._sys_props.regions))
        self.available.observe(self._on_add, names="value")

        col_incl, self.selected = self._make_column("Included", [])
        self.selected.observe(self._on_remove, names="value")

        arrow = widgets.HTML(
            "<span style='font-size:1.5em;'>&rarr;</span>",
            layout=widgets.Layout(flex="0 0 auto", gap="4px")
        )

        children.append(widgets.HBox(
            [col_avail, arrow, col_incl],
            layout=widgets.Layout(
                display="flex",
                width="100%",
                align_items="center",
                justify_content="space-between"
            )
        ))

    @staticmethod
    def _make_column(label_text: str, options) -> tuple[widgets.VBox, widgets.SelectMultiple]:
        """
        Build a labeled SelectMultiple in a VBox, return (vbox, select_widget).
        """
        label = widgets.HTML(label_text)
        sel = widgets.SelectMultiple(
            options=options,
            rows=6,
            layout=widgets.Layout(flex="1 1 auto", min_width="0", width="100%")
        )
        col = widgets.VBox(
            [label, sel],
            layout=widgets.Layout(
                display="flex",
                flex="0 1 45%",
                min_width="0",
                align_items="center",
                align_content="center",
                justify_content="center"
            )
        )
        return col, sel

    def _on_add(self, change):
        """Move selections from available → selected."""
        for name in change["new"]:
            if name not in self._chosen:
                self._chosen.append(name)

        self.available.value = ()
        self.refresh()

    def _on_remove(self, change):
        """Move selections from selected → available."""
        for name in change["new"]:
            if name in self._chosen:
                self._chosen.remove(name)
        self.selected.value = ()
        self.refresh()

    def _on_rebuild(self, _):
        """Re-create the mesh with only the chosen subregions."""
        logger.debug("SelectSubregionsInMesh._on_rebuild: chosen=%r", self._chosen)
        old_mesh = self._sys_props.main_mesh
        if not old_mesh:
            self.btn_rebuild.button_style = "danger"
            return

        subs = {name: self._sys_props.regions[name] for name in self._chosen}

        try:
            new_mesh = df.Mesh(
                region=old_mesh.region,
                cell=self._sys_props.cell,
                subregions=subs,
                bc=getattr(old_mesh, 'bc', '')
            )
        except Exception as e:
            logger.error("SelectSubregionsInMesh._on_rebuild: Rebuild failed: %s", e, exc_info=True)
            self.btn_rebuild.button_style = "danger"
            return

        self.btn_rebuild.button_style = "success"
        logger.success(f"Rebuilt mesh '{self.dd_mesh.value}' with subregions: {self._chosen}")

        if self._ctrl_cb:
            self._ctrl_cb(new_mesh)
