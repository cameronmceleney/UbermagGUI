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
from ipywidgets import Layout
from IPython.display import display

# Third-party imports

# Local application imports
from .scenes.region_lists import RegionListReadOnly

logger = logging.getLogger(__name__)

__all__ = ["OutlinerController"]


class OutlinerController:
    def __init__(self, workspace_controller):
        """
        Parameters
        ----------
        workspace_controller : WorkspaceController
            The top‐level controller owning global state.
        """
        self._wc = workspace_controller
        # region list widget
        self._list = RegionListReadOnly()

        # Subscribe to geometry and system‐init events
        self._wc.register_geometry_listener(self._on_geometry_change)
        self._wc.register_mesh_listener(self._on_mesh_created)
        self._wc.register_init_mag_listener(self._on_init_mag_created)

    def _on_geometry_change(self, main_region, subregions):
        # update with fresh geometry, keep old mesh/init_mag until they change
        self._list.update(
            main_region=main_region,
            subregions=subregions,
            mesh=self._wc.mesh,
            init_mag=self._wc.init_mag
        )

    def _on_mesh_created(self, mesh):
        # update with new mesh
        self._list.update(
            main_region=self._wc.main_region,
            subregions=self._wc.subregions,
            mesh=mesh,
            init_mag=self._wc.init_mag
        )

    def _on_init_mag_created(self, init_mag):
        # update with new initial magnetisation
        self._list.update(
            main_region=self._wc.main_region,
            subregions=self._wc.subregions,
            mesh=self._wc.mesh,
            init_mag=init_mag
        )

    def build(self) -> widgets.Widget:
        """
        Return the Outliner widget to be placed in the interface.
        """
        return self._list.widget

    def refresh(self):
        """
        Force a refresh from current state.
        """
        self._list.update(
            main_region=self._wc.main_region,
            subregions=self._wc.subregions,
            mesh=self._wc.mesh,
            init_mag=self._wc.init_mag
        )
