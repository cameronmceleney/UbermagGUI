#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Project: UbermagGUI
Path:    src/workspaces/workspace_controller.py

Description:
    Top‐level wiring: owns mm.System and mounts each Workspace.
    
Author:      Cameron Aidan McEleney < c.mceleney.1@research.gla.ac.uk >
Created:     12 May 2025
IDE:         PyCharm
Version:     0.1.0
"""

# Standard library imports
import logging
import ipywidgets as widgets
from ipywidgets import Layout
from IPython.display import display

# Third-party imports
import micromagneticmodel as mm

# Local application imports
# you would import, e.g., OutlinerWorkspace, EquationsWorkspace, ViewportWorkspace here
from .initialisation.controllers import GeometryController, SystemInitController
# from .outliner import OutlinerWorkspace
# from .equations.controllers import EnergyController, DynamicsController
# from .viewport.workspace import ViewportWorkspace

__all__ = ["WorkspaceController", "WorkspaceTopMenu"]

logger = logging.getLogger(__name__)


class WorkspaceController:
    """
    Orchestrates the feature‐controllers:
      • GeometryController
      • SystemInitController
      […future: Outliner, Equations, etc.]
    Holds shared state: main_region, subregions, mesh, init_mag.

    The workspace_controller must offer registration methods for listeners:
     - register_geometry_listener(cb)  -> cb(main_region, subregions)
     - register_mesh_listener(cb)      -> cb(mesh)
     - register_init_mag_listener(cb)  -> cb(init_mag)
    """

    def __init__(self, system: mm.System, plot_callback):
        """
        Parameters
        ----------
        system : mm.System
            Your one‐and‐only micromagnetic system.
        plot_callback : callable
            Typically: viewport_area.plot_regions
        """
        self.system = system
        self._plot_callback = plot_callback

        # ——— listeners for external clients (e.g. Outliner) ———
        self._geometry_listeners = []
        self._mesh_listeners = []
        self._init_mag_listeners = []

        # States shared across all Initialisation workspaces
        self.main_region = None
        self.subregions = {}
        self.mesh = None
        self.init_mag = None

        # --- instantiate the two initialisation features ---
        self.geometry_ctrl = GeometryController(
            system=self.system,
            plot_callback=self._plot_regions,
            domain_callback=self._on_domain,
            add_callback=self._add_subregion,
            remove_callback=self._remove_subregion,
            show_domain_getter=lambda: True  # toggle_show could be dynamic
        )

        self.system_init_ctrl = SystemInitController(
            system=self.system,
            plot_callback=self._plot_regions
        )

        self._wire_workspace_controllers()

        # --- (optional) other workspaces I might add later ---
        # self.equations_ws = EquationsWorkspace(self)

        # build our top‐level menu of workspaces
        self.workspaces = {
            'Geometry':    self.geometry_ctrl,
            'System Init': self.system_init_ctrl,
            # 'Equations':   self.equations_ws,
        }
        self.selector = widgets.ToggleButtons(
            options=list(self.workspaces),
            description='Workspace:',
            layout=Layout(width='auto'),
            style={'button_width': '10ch'}
        )
        self.selector.observe(self._on_workspace_change, names='value')

        self.output = widgets.Output(layout=Layout(overflow='auto'))

    def _wire_workspace_controllers(self):
        # wire the "mesh created" and "field defined" callbacks
        self.system_init_ctrl.panels['Mesh'].set_state_callback(self._on_mesh_created)
        self.system_init_ctrl.panels['Initial fields'].set_state_callback(self._on_init_mag_created)
        self.system_init_ctrl.panels['Subregions in mesh'].set_state_callback(self._on_mesh_created)

    def _on_workspace_change(self, change):
        if change['name'] == 'value':
            self.render()

    def render(self):
        """Re‐mount the currently selected workspace into our output area."""
        ws = self.workspaces[self.selector.value]
        self.output.clear_output()
        with self.output:
            display(ws.build())

    def build(self):
        """Return the assembled menu + workspace pane."""
        # select first tab to get content populated
        self.selector.value = list(self.workspaces)[0]
        self.render()
        return widgets.VBox(
            [self.selector, self.output],
            layout=Layout(width='100%', height='100%')
        )

    def build_selector_for_top_menu(self):
        """Intentionally separated out the selector bar for the TopMenu UI area"""
        container = widgets.HBox(
            children=[self.selector],
            layout=widgets.Layout(justify_content='flex-start')
        )
        return container

    # — plot proxy —
    def _plot_regions(self, main_region, subregions, show_domain=True):
        if self._plot_callback:
            self._plot_callback(main_region, subregions, show_domain)

        # notify geometry listeners
        for cb in self._geometry_listeners:
            cb(main_region, subregions)

    # ---- geometry state mutators  ----
    def _on_domain(self, region):
        self.main_region = region
        self.subregions.clear()
        self._after_geometry_change()

    def _add_subregion(self, subregion_name: str, region):
        self.subregions[subregion_name] = region
        self._after_geometry_change()

    def _remove_subregion(self, subregion_name: str):
        self.subregions.pop(subregion_name, None)
        self._after_geometry_change()

    def _after_geometry_change(self):
        """
        Run after main_region or subregions change:
         - redraw the viewport
         - (if you had an outliner workspace, refresh it here)
        """
        self._plot_regions(self.main_region, self.subregions, True)

    # ---- system‐init state mutators ----
    def _on_mesh_created(self, mesh):
        logger.success("WorkspaceController got mesh: %r", mesh)
        self.mesh = mesh
        # notify mesh listeners
        for cb in self._mesh_listeners:
            cb(mesh)

        # notify geometry controller to sync base-mesh options in DropDown widget
        if hasattr(self.system_init_ctrl, 'refresh_mesh_dropdown'):
            self.system_init_ctrl.refresh_mesh_dropdown()

    def _on_init_mag_created(self, field):
        logger.success("WorkspaceController got init‐mag: %r", field)
        self.init_mag = field

        for cb in self._init_mag_listeners:
            cb(field)

    # ——— registration API for external listeners ———
    def register_geometry_listener(self, cb):
        """cb(main_region, subregions) called whenever geometry changes."""
        self._geometry_listeners.append(cb)

    def register_mesh_listener(self, cb):
        """cb(mesh) called whenever a mesh is created."""
        self._mesh_listeners.append(cb)

    def register_init_mag_listener(self, cb):
        """cb(init_mag) called whenever initial magnetisation is defined."""
        self._init_mag_listeners.append(cb)

class WorkspaceTopMenu:
    def __init__(self):
        self.view = None
