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
from ipywidgets import Layout
from IPython.display import display
import typing

# Third-party imports
import micromagneticmodel as mm
import discretisedfield as df

# Local application imports
from src.workspaces.initialisation.controllers import InitialisationController
from src.config.dataclass_containers import _CoreProperties
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

    def __init__(
            self,
            properties_controller: _CoreProperties,
            plot_callback,
    ):
        """
        Parameters
        ----------
        properties_controller:
            Core interface instances inc. mm.System
        plot_callback :
            Typically: viewport_area.plot_regions
        """
        self._props_controller = properties_controller
        self._plot_callback = plot_callback

        # ——— listener lists for any outside subscriber (e.g. OutlinerController) ———
        self._geometry_listeners: typing.List[typing.Callable[[df.Region, typing.Dict[str, df.Region]], None]] = []
        self._mesh_listeners: typing.List[typing.Callable[[df.Mesh], None]] = []
        self._init_mag_listeners: typing.List[typing.Callable[[df.Field], None]] = []

        self.workspaces = {
            'Initialisation': InitialisationController(
                properties_controller=self._props_controller,
                workspace_controller=self,
                domain_callback=self._on_domain,
                add_callback=self._add_subregion,
                remove_callback=self._remove_subregion,
                mesh_callback=self._on_mesh_created,
                init_mag_callback=self._on_init_mag_created,
            )
        }

        self.selector = widgets.ToggleButtons(
            options=list(self.workspaces),
            value='Initialisation',
            description='Workspace:',
            layout=Layout(width='auto'),
            style={'button_width': '10ch'}
        )
        self.selector.observe(self._on_workspace_change, names='value')

        self.output = widgets.Output(layout=Layout(
            width='100%', height='100%', min_height='0', overflow_x='hidden', overflow_y='auto'))

    def _on_workspace_change(self, change):
        if change['name'] == 'value':
            self.render()

    def render(self):
        """Re‐mount the currently selected workspace into our output area."""
        ws = self.workspaces[self.selector.value]
        self.output.clear_output()
        with self.output:
            display(ws.build())

    def build(self) -> widgets.Output:
        """Return the assembled menu + workspace pane."""
        # select first tab to get content populated
        # initialize selection only once
        if not hasattr(self, '_initialized'):
            self.selector.value = list(self.workspaces.keys())[0]
        # render the currently‐selected sub‐workspace into self.output
        self.render()

        return self.output

    def build_selector_for_top_menu(self):
        """Intentionally separated out the selector bar for the TopMenu UI area"""
        container = widgets.HBox(
            children=[self.selector],
            layout=widgets.Layout(justify_content='flex-start')
        )
        return container

    # ——— registration API for external listeners ———
    def register_geometry_listener(self, cb: typing.Callable):
        self._geometry_listeners.append(cb)

    # — plot proxy —
    def _plot_regions(self, main_region: df.Region, subregions: dict[str, df.Region], show_domain: bool = True):
        """Wired to ViewpointsController.plot_regions"""
        logger.debug("WorkspaceController._plot_regions: attempting to update Viewports area" )
        if self._plot_callback:
            self._plot_callback(main_region, subregions, show_domain)

        # notify geometry subscribers too
        for cb in self._geometry_listeners:
            cb(main_region, subregions)

        logger.success("WorkspaceController._plot_regions:")

    # ---- geometry state mutators  ----
    def _on_domain(self, region):
        logger.debug("WorkspaceController._on_domain: got new domain %r", region)
        self._props_controller._main_region = region

        try:
            self._after_geometry_change()
        except Exception:
            logger.exception("WorkspaceController._on_domain: Error while redrawing after domain change")

        logger.success("WorkspaceController._on_domain: set new domain %r", region)

    def _add_subregion(self, subregion_name: str, region):
        logger.debug("WorkspaceController._add_subregion: got new region [%r] %r",
                     subregion_name, region)
        self._props_controller._add_region(subregion_name, region)

        try:
            self._after_geometry_change()
        except Exception:
            logger.exception("WorkspaceController._add_subregion: Error while redrawing after adding a region.")

        logger.success("WorkspaceController._add_subregion: added new region [%r] %r", subregion_name, region)

    def _remove_subregion(self, subregion_name: str):
        logger.debug("WorkspaceController._remove_subregion: got removal request for region [%r]",
                     subregion_name)
        self._props_controller._remove_region(subregion_name)

        try:
            self._after_geometry_change()
        except Exception:
            logger.exception("WorkspaceController._remove_subregion: Error while redrawing after removing a region.")

        logger.success("WorkspaceController._remove_subregion: removed region [%r].", subregion_name)

    def _after_geometry_change(self):
        """
        Run after main_region or subregions change:
         - redraw the viewport
         - (if you had an outliner workspace, refresh it here)
        """
        #for cb in self._geometry_listeners:
        #    cb(self._props_controller.main_region, self._props_controller.regions)
        self._plot_regions(self._props_controller.main_region, self._props_controller.regions, True)

    # ---- system‐init state mutators ----
    def _on_mesh_created(self, mesh):
        logger.success("WorkspaceController got mesh: %r", mesh)
        self._props_controller._main_mesh = mesh

        # notify mesh subscribers
        for cb in self._mesh_listeners:
            cb(mesh)

        # notify geometry controller to sync base-mesh options in DropDown widget
        # if hasattr(self.workspaces, 'refresh_mesh_dropdown'):
        #    self.system_init_ctrl.refresh_mesh_dropdown()

    def register_mesh_listener(self, cb: typing.Callable):
        self._mesh_listeners.append(cb)

    def _on_init_mag_created(self, field):
        logger.success("WorkspaceController got init‐mag: %r", field)
        self._props_controller._set_initial_magnetisation(field)

        # notify init‐mag subscribers
        for cb in self._init_mag_listeners:
            cb(field)

    def register_init_mag_listener(self, cb: typing.Callable):
        self._init_mag_listeners.append(cb)


class WorkspaceTopMenu:
    def __init__(self):
        self.view = None
