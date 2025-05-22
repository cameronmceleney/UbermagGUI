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
import typing

# Third-party imports
import discretisedfield as df

# Local application imports
from src.workspaces.initialisation.controllers import InitialisationGroupFeatureController
from src.workspaces.equations.controllers import EquationsGroupFeatureController
from src.config.dataclass_containers import _CoreProperties

__all__ = ["WorkspaceController", "WorkspaceTopMenu"]

logger = logging.getLogger(__name__)


class WorkspaceController:
    """
    Orchestrates the feature‐controllers:
      • GeometryFeatureController
      • SystemInitFeatureController
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

        # Used by builder.py to track initial pass over interface areas
        self._has_built_once = False

        # --- listeners to features for any outside subscriber ---
        # (e.g. Geometry, Mesh -> OutlinerController, Geometry->Mesh)
        self._geometry_listeners: typing.List[typing.Callable[[df.Region, typing.Dict[str, df.Region]], None]] = []
        self._mesh_listeners: typing.List[typing.Callable[[df.Mesh], None]] = []
        self._init_mag_listeners: typing.List[typing.Callable[[df.Field], None]] = []
        self._energy_listeners: typing.List[typing.Callable[[typing.Any], None]] = []
        self._dynamics_listeners: typing.List[typing.Callable[[typing.Any], None]] = []

        self.workspace_features = {
            'Initialisation': InitialisationGroupFeatureController(
                properties_controller=self._props_controller,
                workspace_controller=self,
                domain_callback=self._on_domain,
                add_callback=self._add_subregion,
                remove_callback=self._remove_subregion,
                mesh_callback=self._on_mesh_created,
                init_mag_callback=self._on_init_mag_created,
            ),
            # TODO. Check if lazy-import is better here to avoid circular imports
            'Equations': EquationsGroupFeatureController(
                properties_controller=self._props_controller,
                workspace_controller=self,
                energy_callback=self._on_energy_term,
                dynamics_callback=self._on_dynamics_term,
            )
        }

        self.workspace_selector = widgets.ToggleButtons(
            options=list(self.workspace_features),
            value='Initialisation',
            description='Workspace:',
            layout=widgets.Layout(width='auto', overflow='hidden'),
            style={'button_width': '10ch'}
        )
        self.workspace_selector.observe(self._on_workspace_change, names='value')

        self.workspace_container: typing.Optional[widgets.Box] = None

    def _on_workspace_change(self, change):
        if change['name'] == 'value':
            self._update_container()

    def _update_container(self):
        """Internal API for swapping in the new workspace widget."""
        ws = self.workspace_features[self.workspace_selector.value]
        # build the new workspace panel
        ws_panel = ws.build()
        # replace the sole child of our container
        self.workspace_container.children = (ws_panel,)

    def build(self) -> widgets.Box:
        """
        Public API that constructs a single ``Box`` container for the WorkspaceController.

        This container is directly injected into the overall ``UbermagInterface`` ``GridspecLayout``.
        """
        if not self._has_built_once:
            # Select initial workspace
            self.workspace_selector.value = list(self.workspace_features.keys())[0]
            self._has_built_once = True

            # Hosts dynamic content from Workspace area of interface
            self.workspace_container = widgets.Box(
                layout=widgets.Layout(
                    display='flex',
                    flex='1 1 0',  # Grow to fill all the remaining space given to the Workspace area
                    min_height='0',
                    overflow='hidden'  # No scroll bars; let children handle internal scrolls
                )
            )

        # render the sub‐workspace while updating to its default feature + panel selection
        self._update_container()

        return self.workspace_container

    def build_selector_for_top_menu(self):
        """Intentionally separated out the selector bar for the TopMenu UI area"""
        container = widgets.HBox(
            children=[self.workspace_selector],
            layout=widgets.Layout(justify_content='flex-start')
        )
        return container

    # ——— registration API for external listeners ———
    def register_geometry_listener(self, cb: typing.Callable):
        """
        Notify subscribers whenever the `Geometry` feature creates/modifies a term.

        Examples include: adding a region to the domain; creating a new region.
        """
        self._geometry_listeners.append(cb)

    def register_mesh_listener(self, cb: typing.Callable):
        """
        Notify subscribers whenever the `System Init.` feature creates/modifies a term.

        Examples include: creating a mesh; changing a region's subregions.
        """
        self._mesh_listeners.append(cb)

    def register_init_mag_listener(self, cb: typing.Callable):
        """
        Notify subscribers whenever the `System Init.` feature creates/modifies the ``mm.System`` container in
        the main `_CoreProperties` instance.
        """
        self._init_mag_listeners.append(cb)

    def register_energy_listener(self, cb: typing.Callable[[typing.Any], None]):
        """Notify subscribers whenever an Energy term is created/modified."""
        self._energy_listeners.append(cb)

    def register_dynamics_listener(self, cb: typing.Callable[[typing.Any], None]):
        """Notify subscribers whenever a Dynamics term is created/modified."""
        self._dynamics_listeners.append(cb)

    # — plot proxy —
    def _plot_regions(self, main_region: df.Region, subregions: dict[str, df.Region], show_domain: bool = True):
        """Wired to ViewpointsController.plot_regions"""
        logger.debug("WorkspaceController._plot_regions: attempting to update Viewports area")
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
        self._plot_regions(self._props_controller.main_region, self._props_controller.regions, True)

    # ---- system‐init state mutators ----
    def _on_mesh_created(self, mesh):
        logger.success("WorkspaceController got mesh: %r", mesh)
        self._props_controller._main_mesh = mesh

        # notify mesh subscribers
        for cb in self._mesh_listeners:
            cb(mesh)

    def _on_init_mag_created(self, field):
        logger.success("WorkspaceController got init‐mag: %r", field)
        self._props_controller._set_initial_magnetisation(field)

        # notify init‐mag subscribers
        for cb in self._init_mag_listeners:
            cb(field)

    # ---- equations state mutators ----
    def _on_energy_term(self, term):
        """Called by EquationsGroupFeatureController when an energy term is set."""
        # notify energy subscribers
        for cb in self._energy_listeners:
            cb(term)

    def _on_dynamics_term(self, term):
        """Called by EquationsGroupFeatureController when a dynamics term is set."""
        # notify dynamics subscribers
        for cb in self._dynamics_listeners:
            cb(term)


class WorkspaceTopMenu:
    def __init__(self):
        self.view = None
