#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Project: UbermagGUI
Path:    src/workspaces/initialisation/controllers.py

GeometryController:
    Hosts the “Domain / Place / Append / Remove” panels.
    Formerly self.panels_model + _build_model_creation_panel.

SystemInitController:
    Hosts the “Mesh / Initial fields / Subregions” panels.
    Formerly self.panels_system_init + _build_system_initiation_tab.

HandleFeature:
    Abstract base to build a toggle-selector + content region for a group of panels.

Author:      Cameron Aidan McEleney < c.mceleney.1@research.gla.ac.uk >
Created:     12 May 2025
IDE:         PyCharm
Version:     0.1.0
"""

# Standard library imports
import ipywidgets as widgets
from ipywidgets import Layout
from IPython.display import display
import logging

# Third-party imports
import discretisedfield as df

# Local application imports
from . import domain, regions, fields, meshes

logger = logging.getLogger(__name__)


__all__ = [
    "HandleFeature",
    "GeometryController",
    "SystemInitController"
]


class HandleFeature:
    def __init__(self):
        """
        Parent abstract class to help with buildings features that controllers will manage.
        """
        self.panels = {}
        self.content = widgets.Output(layout=Layout(overflow='auto'))
        self.selector = None

    def build_feature(self, panel_titles):
        names = list(panel_titles.keys())

        # Guaranteeing widths will be particularly helpful when displaying icons
        min_width = str(min(max(len(n) for n in names), 8) + 2) + "ch"

        selector = widgets.ToggleButtons(
            options=names,
            tooltips=tuple(names),
            button_style='',
            style={
                'button_width': min_width,
                'align_content': 'center',
                'justify_content': 'center'
            },
            layout=Layout(
                min_width=min_width,
                width='auto', height='100%',
                overflow='auto',
                display='flex', # required for column-nowrap to take effect
                flex_flow='column nowrap'
            ),
        )

        self.selector.observe(self._on_select, names='value')
        self.selector.value = names[0]  # initial

        grid = widgets.GridspecLayout(n_rows=1, n_columns=2,
                                      layout=Layout(
                                          width='100%',
                                          height='100%',
                                          gap='4px',
                                      )
                              )

        # 1st column follows own Layout, and 2nd column fills remaining space
        grid._grid_template_columns = f'{min_width} 1fr'

        grid[0, 0] = selector
        grid[0, 1] = self.content

        return grid

    def _on_select(self, change: dict):
        if change.get('name') == 'value':
            self.content.clear_output()
            with self.content:
                display(self.panels[change['new']].build(self))


class GeometryController(HandleFeature):
    def __init__(
            self,
            system,
            plot_callback,
            domain_callback,
            add_callback,
            remove_callback,
            show_domain_getter
    ):
        super().__init__()
        self.system = system
        self.plot_callback = plot_callback
        self.domain_cb = domain_callback
        self.add_cb = add_callback
        self.remove_cb = remove_callback
        self.show_domain_getter = show_domain_getter

        # All panels in feature
        self.panels = {
            'Domain': domain.DefineDomainRegion(),
            'Place':  regions.PlaceRegion(),
            'Append': regions.AppendRegionUsingBase(),
            'Remove': regions.RemoveRegion()
        }

        self._wire_panel_callbacks()

    def _wire_panel_callbacks(self):
        self.panels['Domain'].set_state_callback(self.domain_cb)
        self.panels['Domain'].set_plot_callback(self.plot_callback)

        self.panels['Place'].set_state_callback(self.add_cb)
        self.panels['Place'].set_plot_callback(self.plot_callback)

        self.panels['Append'].set_state_callback(self.add_cb)
        self.panels['Append'].set_plot_callback(self.plot_callback)

        self.panels['Remove'].set_state_callback(self.remove_cb)
        self.panels['Remove'].set_plot_callback(self.plot_callback)

    def build(self):
        return self.build_feature(self.panels)


class SystemInitController(HandleFeature):
    def __init__(self, system, plot_callback):
        super().__init__()
        self.system = system
        self.plot_callback = plot_callback

        # panels for each step
        self.panels = {
            'Mesh': meshes.CreateMesh(),
            'Initial fields': fields.DefineSystemInitialMagnetisation(),
            'Subregions in mesh': meshes.SelectSubregionsInMesh()
        }

        self._wire_panel_callbacks()

    def _wire_panel_callbacks(self):
        """wire state + plot"""
        self.panels['Mesh'].set_state_callback(self._on_mesh)

        self.panels['Initial fields'].set_state_callback(self._on_field)

        self.panels['Subregions in mesh'].set_state_callback(self._on_mesh)

    def build(self):
        return self.build_feature(self.panels)

    def _on_mesh(self, mesh):

        logger.success("ControlsPanel received mesh: %r", mesh)

        self.system.mesh = mesh  # Store the new mesh

        # update the mesh dropdown in System‑Init tab
        self.refresh_mesh_dropdown()

    def _on_field(self, field):
        self.system.m = field

    def refresh_mesh_dropdown(self):
        """
        Keep the MeshPanel’s base‐region dropdown in sync.
        """
        mesh_panel = self.panels.get('Mesh')
        if not mesh_panel:
            return
        # bases = ['main'] + all subregion names, but only once main_region exists
        if self.system.main_region is None:
            mesh_panel.dd_base_region.options = []
            mesh_panel.dd_base_region.value = None
        else:
            bases = ['main'] + list(self.system.subregions.keys())
            mesh_panel.refresh(bases)

        init_mag_panel = self.panels.get("Initial fields")
        if not init_mag_panel:
            return
        if init_mag_panel is not None:
            init_mag_panel.refresh()

        subregions_panel = self.panels.get("Subregions in mesh")
        if not subregions_panel:
            return
        if subregions_panel is not None:
            subregions_panel.refresh()
