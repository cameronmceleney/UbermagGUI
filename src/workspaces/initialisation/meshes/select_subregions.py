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
from ipywidgets import Layout

# Third-party imports
import discretisedfield as df

# Local application imports

__all__ = ["SelectSubregionsInMesh"]

logger = logging.getLogger(__name__)


class SelectSubregionsInMesh:
    def __init__(self):
        self._mesh_cb = None
        self._sys_props = None

        # widgets
        self.dd_mesh = None
        self.available = None
        self.selected = None
        self.btn_rebuild = None

        # internal set of currently chosen subregions
        self._chosen = []

    def set_state_callback(self, cb):
        """Register callback to receive the new df.Mesh."""
        self._mesh_cb = cb

    def build(self, context) -> widgets.VBox:
        """Build the UI for selecting subregions and rebuilding mesh."""
        self._sys_props = context
        logger.debug("SelectSubregionsInMesh.build: constructing UI")

        panel = widgets.VBox(
            layout=widgets.Layout(
                width='auto',
                height='auto',
                overflow="hidden",
                padding="4px"
            ),
        )
        children = []

        children.append(widgets.HTML("<b>Include/exclude subregions</b>"))
        children.append(widgets.HTML("Select which defined regions to include:"))

        html_base_mesh = widgets.HTML(
            "For a given base mesh",
            layout=widgets.Layout(flex='0 0 auto')
        )

        # TODO. Currently only accepting main_mesh; need to scale to all possible domain
        self.dd_mesh = widgets.Dropdown(layout=widgets.Layout(flex="0 0 30%"))
        self.dd_mesh.observe(self._on_mesh_select, names="value")

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

        # Two SelectMultiple in column-view: Available v. Included regions in mesh
        self._build_selection_boxes(children)

        self.btn_rebuild = widgets.Button(description="Rebuild Mesh", button_style="primary",)
        self.btn_rebuild.on_click(self._on_rebuild)
        children.append(widgets.HBox([self.btn_rebuild], layout=Layout(justify_content="center")))

        panel.children = tuple(children)

        self.refresh()

        return panel

    def _on_mesh_select(self, change):
        """When they pick a mesh, seed ``_chosen`` from its .subregions."""
        new = change['new']
        logger.debug("SelectSubregionsInMesh._on_mesh_select: %r", new)
        if new and self._sys_props.main_mesh:
            # grab whatever subregions the mesh currently has
            self._chosen = list(self._sys_props.main_mesh.subregions.keys())
        else:
            self._chosen = []
        self.refresh()

    def refresh(self, *_):
        """
        Refresh both lists when controls.subregions or controls.mesh changes.
        """
        # mesh dropdown
        if not getattr(self, "_sys_props", None) or self.dd_mesh is None:
            return

        has_mesh = bool(self._sys_props and self._sys_props.main_mesh)

        # TODO. List of domain will be dynamic in the future.
        # (Re)Set mesh dropdown here, else panel omits current mesh's subregion(s)
        opts = [] if not has_mesh else [("main", "main")]
        old = self.dd_mesh.value
        self.dd_mesh.options = opts

        if old not in {v for _, v in opts}:
            self.dd_mesh.value = None

        self.btn_rebuild.disabled = not has_mesh

        # 3) lists: available = defined minus chosen; included = chosen
        all_names = list(self._sys_props.regions.keys())
        self.available.options = [n for n in all_names if n not in self._chosen]
        # selected = exactly the mesh’s current chosen
        self.selected.options = self._chosen

    def _on_add(self, change):
        """Move selections from available → selected."""
        for name in change["new"]:
            if name not in self._chosen:
                self._chosen.append(name)
        # clear selection and refresh
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

        if self._mesh_cb:
            self._mesh_cb(new_mesh)

    def _build_selection_boxes(self, panel_children):
        """
        Append to panel_children an HBox of
        [ Available-column | → | Included-column ] where each column
        is a VBox(label over SelectMultiple).
        """
        html_selection_process = widgets.HTML(
            value=", choose which regions to include as the mesh's subregions. "
                  "It's the responsibility of the user to ensure that the subregions are "
                  "defined appropriately. ",
            layout=widgets.Layout(
                flex='1 1 auto',
                min_width='0',
                overflow='visible'
            )
        )
        panel_children.append(html_selection_process)

        # Available column
        col_avail, self.available = self._make_column(
            "Available", list(self._sys_props.regions)
        )
        self.available.observe(self._on_add, names="value")

        # Included column
        col_incl, self.selected = self._make_column(
            "Included", []
        )
        self.selected.observe(self._on_remove, names="value")

        # Arrow
        arrow = widgets.HTML(
            "<span style='font-size:1.5em;'>&rarr;</span>",
            layout=Layout(
                flex='0 0 auto',
                gap='5%'
            )
        )

        # One row to hold them
        row = widgets.HBox(
            children=[col_avail, arrow, col_incl],
            layout=Layout(
                display='flex',
                width='100%',
                align_items='center',
                justify_content='space-between',
            )
        )
        panel_children.append(row)

    @staticmethod
    def _make_column(label_text: str, options):
        """Return (column_vbox, select_widget)."""
        label = widgets.HTML(label_text)
        sel = widgets.SelectMultiple(
            options=options,
            rows=6,
            layout=Layout(
                flex='1 1 auto',
                min_width='0',
                width='100%',
            )
        )
        col = widgets.VBox(
            children=[label, sel],
            layout=Layout(
                display='flex',
                flex='0 1 45%',
                min_width='0',
                align_items='center', align_content='center',
                justify_content='center'
            )
        )
        return col, sel
