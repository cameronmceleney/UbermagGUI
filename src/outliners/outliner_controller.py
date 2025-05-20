#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Project: UbermagGUI
Path:    src/outliners/outliner_controller.py

OutlinerController:
  - Orchestrates the read-only region list feature.
  - Subscribes to state changes in the workspace controller.
    
Author:      Cameron Aidan McEleney < c.mceleney.1@research.gla.ac.uk >
Created:     13 May 2025
IDE:         PyCharm
Version:     0.1.0
"""

# Standard library imports
import logging
import ipywidgets as widgets

# Third-party imports

# Local application imports
from .scenes.region_lists import RegionListReadOnly

__all__ = ["OutlinerController"]

logger = logging.getLogger(__name__)


class OutlinerController:
    def __init__(self, properties_controller, workspace_controller):
        """
        Orchestrates the read-only region list feature.

        Parameters
        ----------
        properties_controller : _CoreProperties
            Shared state container (meshes, regions, etc.)
        workspace_controller : WorkspaceController
            Top-level controller to subscribe for events.
        """
        self._props = properties_controller
        self._wc = workspace_controller
        logger.debug("OutlinerController: initialising.")

        # region list widget
        self._list = RegionListReadOnly()

        # Subscribe only geometry; other handlers are placeholders
        self._wc.register_geometry_listener(self._on_geometry_change)
        self._wc.register_mesh_listener(self._on_geometry_change)

        # Initial snapshot
        self.refresh()

    def _on_geometry_change(self, *args, **kwargs):
        """Callback for geometry changes: update using current props."""
        logger.debug("OutlinerController._on_geometry_change: args=%r, kwargs=%r", args, kwargs)

        # Determine active mesh name (first in dict) or None
        mesh_names = list(self._props.meshes.keys())
        mesh_name = mesh_names[0] if mesh_names else None

        # Determine main region name under domain_key
        main_region = self._props.main_region
        region_name = None
        if main_region is not None:
            # domain_key is 'main'
            region_name = self._props._domain_key

        subregion_names = [n for n in self._props.regions.keys() if n != self._props._domain_key]

        self._list.update(
            mesh_name=mesh_name,
            region_name=region_name,
            subregions=subregion_names
        )
        logger.success("OutlinerController._on_geometry_change: geometry outliner updated (mesh=%r).", mesh_name)

    @staticmethod
    def _on_mesh_created(self, mesh, *args, **kwargs):
        logger.debug("OutlinerController._on_mesh_created: mesh=%r (not yet handled).", mesh)

    @staticmethod
    def _on_init_mag_created(self, init_mag, *args, **kwargs):
        logger.debug("OutlinerController._on_init_mag_created: init_mag=%r (not yet handled).", init_mag)

    def build(self) -> widgets.Box:
        """
        Return the Outliner widget to be placed in the interface.

        Defaults to setting this Box as 30% the total height of its parent.
        """
        box = widgets.Box(
            children=[self._list.widget],
            layout=widgets.Layout(
                display='flex',
                flex='0 0 30%',  # Note! Use of 'fr' here leads to improper scaling. Use percentages
                min_height='0',
                overflow='hidden'
            )
        )

        return box

    def refresh(self):
        logger.debug("OutlinerController.refresh(): performing initial update.")
        # Simply re-use geometry handler
        self._on_geometry_change()
