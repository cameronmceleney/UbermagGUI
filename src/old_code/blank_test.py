#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Project: UbermagGUI
Path:    src/workspaces/initialisation/meshes/select_subregions.py

SelectSubregionsInMesh:
    UI to include/exclude subregions in a given df.Mesh.
"""
import logging
import ipywidgets as widgets
from ipywidgets import Layout
import discretisedfield as df

logger = logging.getLogger(__name__)

__all__ = ["SelectSubregionsInMesh"]


class SelectSubregionsInMesh:
    def __init__(self):
        self._mesh_cb = None
        self._sys_props = None

        self.dd_mesh = None
        self.available = None
        self.selected = None
        self.btn_rebuild = None

        self._chosen = []

    def set_state_callback(self, cb):
        """Register callback to receive the new df.Mesh."""
        self._mesh_cb = cb

    def build(self, context) -> widgets.VBox:
        self._sys_props = context
        logger.debug("SelectSubregionsInMesh.build: constructing UI")

        panel = widgets.VBox(layout=widgets.Layout(overflow="auto", padding="4px"))
        children = []

        children.append(widgets.HTML("<b>Include/exclude subregions</b>"))
        children.append(widgets.HTML("Select which defined regions to include:"))

        # mesh dropdown
        self.dd_mesh = widgets.Dropdown(layout=Layout(width="50%"))
        self.dd_mesh.observe(self._on_mesh_select, names="value")
        children.append(widgets.HBox([widgets.HTML("Mesh:"), self.dd_mesh],
                                     layout=widgets.Layout(justify_content='space-between')))

        # two columns: Available v. Included
        self._build_selection_boxes(children)

        # rebuild button
        self.btn_rebuild = widgets.Button(description="Rebuild Mesh", button_style="primary")
        self.btn_rebuild.on_click(self._on_rebuild)
        children.append(widgets.HBox([self.btn_rebuild], layout=Layout(justify_content="center")))

        panel.children = tuple(children)

        # initial populate
        self.refresh()
        return anel

    def refresh(self, *_):
        """Refresh mesh dropdown & listboxes from _CoreProperties."""
        main_mesh = self._sys_props.main_mesh
        mesh_opts = [] if not main_mesh else [("Main mesh", "main")]
        logger.debug("SelectSubregionsInMesh.refresh: mesh_opts=%r, regions=%r",
                     mesh_opts, list(self._sys_props.regions.keys()))

        old = self.dd_mesh.value
        self.dd_mesh.options = mesh_opts
        self.dd_mesh.value = old if old in {v for _, v in mesh_opts} else None
        self.btn_rebuild.disabled = not bool(main_mesh)

        # available vs chosen
        all_names = list(self._sys_props.regions.keys())
        self.available.options = [n for n in all_names if n not in self._chosen]
        self.selected.options = self._chosen

    def _on_mesh_select(self, change):
        new = change.get("new")
        logger.debug("SelectSubregionsInMesh._on_mesh_select: %r", new)
        if new and self._sys_props.main_mesh:
            self._chosen = list(self._sys_props.main_mesh.subregions.keys())
        else:
            self._chosen = []
        self.refresh()

    def _on_rebuild(self, _):
        logger.debug("SelectSubregionsInMesh._on_rebuild: chosen=%r", self._chosen)
        old = self._sys_props.main_mesh
        if not old:
            self.btn_rebuild.button_style = "danger"
            return

        subs = {n: self._sys_props.regions[n] for n in self._chosen}
        try:
            new_mesh = df.Mesh(region=old.region,
                               cell=self._sys_props.cell,
                               subregions=subs,
                               bc=getattr(old, "bc", ""))
        except Exception as e:
            logger.error("Rebuild failed: %s", e, exc_info=True)
            self.btn_rebuild.button_style = "danger"
            return

        self.btn_rebuild.button_style = "success"
        logger.success("Rebuilt mesh with subregions %r", self._chosen)
        if self._mesh_cb:
            self._mesh_cb(new_mesh)

    def _build_selection_boxes(self, children):
        # Available
        col_avail, self.available = self._make_column("Available", [])
        self.available.observe(lambda ch: None, names="value")
        # Included
        col_incl, self.selected = self._make_column("Included", [])
        self.selected.observe(lambda ch: None, names="value")

        arrow = widgets.HTML("<span style='font-size:1.5em;'>&rarr;</span>")
        children.append(widgets.HBox([col_avail, arrow, col_incl],
                                     layout=Layout(justify_content='space-between')))

    @staticmethod
    def _make_column(label, options):
        sel = widgets.SelectMultiple(options=options, rows=6)
        col = widgets.VBox([widgets.HTML(label), sel])
        return col, sel