#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Project: UbermagGUI
Path:    src/workspaces/initialisation/controllers.py

InitialisationController:
    Bundles GeometryController & SystemInitController under a Tab.

GeometryController:
    Hosts the “Domain / Place / Append / Remove” panels.
    Formerly self.panels_model + _build_model_creation_panel.

SystemInitController:
    Hosts the “Mesh / Initial fields / Subregions” panels.
    Formerly self.panels_system_init + _build_system_initiation_tab.

Author:      Cameron Aidan McEleney < c.mceleney.1@research.gla.ac.uk >
Created:     12 May 2025
IDE:         PyCharm
Version:     0.1.0
"""
from __future__ import annotations

# Standard library imports
import ipywidgets as widgets
import logging
from typing import Any, Optional

# Third-party imports

# Local application imports
from src.workspaces.utils import SingleFeatureController, GroupFeatureController
from . import domain, regions, fields, meshes

logger = logging.getLogger(__name__)


__all__ = [
    "GeometryController",
    "SystemInitController",
    "InitialisationController"
]


class GeometryController(SingleFeatureController):
    def __init__(
            self,
            properties_controller,
            workspace_controller,
            domain_callback,
            add_callback,
            remove_callback,
    ):
        super().__init__(properties_controller)

        # All panels in feature
        self.panels = {
            'Domain': domain.DefineDomainRegion(),
            'Place':  regions.PlaceRegion(),
            'Append': regions.AppendRegionUsingBase(),
            'Remove': regions.RemoveRegion()
        }

        self.panels['Domain'].set_state_callback(domain_callback)
        self.panels['Place'].set_state_callback(add_callback)
        self.panels['Append'].set_state_callback(add_callback)
        self.panels['Remove'].set_state_callback(remove_callback)

        # Dependents that need to monitor changes in regions.
        workspace_controller.register_geometry_listener(
            lambda main, subs: self.panels['Remove'].refresh()
        )

    def build(self) -> widgets.GridspecLayout:
        return self.build_feature(self.panels)


class SystemInitController(SingleFeatureController):
    def __init__(
            self,
            properties_controller,
            workspace_controller,
            mesh_callback,
            init_mag_callback,
            ):
        super().__init__(properties_controller)

        # panels for each step
        self.panels = {
            'Mesh': meshes.CreateMesh(),
            'Initial fields': fields.DefineSystemInitialMagnetisation(),
            'Subregions in mesh': meshes.SelectSubregionsInMesh()
        }

        # wire their state callbacks
        self.panels['Mesh'].set_state_callback(mesh_callback)
        self.panels['Initial fields'].set_state_callback(init_mag_callback)
        self.panels['Subregions in mesh'].set_state_callback(mesh_callback)

        # *** subscribe to geometry/mesh changes so dropdowns stay in sync ***
        # whenever a region is defined or removed:
        workspace_controller.register_geometry_listener(
            lambda main, subs: self.panels['Mesh'].refresh()
        )

        # whenever a mesh is built or rebuilt:
        workspace_controller.register_mesh_listener(
            lambda mesh, subs: (self.panels['Initial fields'].refresh(),
                          self.panels['Subregions in mesh'].refresh()
                          )
        )

        # TODO. Fix the horrid refresh arg.
        workspace_controller.register_mesh_listener(
            lambda mesh: self.panels['Mesh'].refresh()
        )

    def build(self) -> widgets.GridspecLayout:
        return self.build_feature(self.panels)


class InitialisationController(GroupFeatureController):
    def __init__(
            self,
            # access to top-level shared attributes
            properties_controller,
            workspace_controller,
            # callbacks from top‐level WorkspaceController:
            domain_callback,
            add_callback,
            remove_callback,
            mesh_callback,
            init_mag_callback,
    ):
        # Exposes Geometry + System‐Init features under one Tab widget.

        # instantiate each feature; wired handled by feature's controller
        self.features = {
            'Geometry': GeometryController(
                properties_controller=properties_controller,
                workspace_controller=workspace_controller,
                domain_callback=domain_callback,
                add_callback=add_callback,
                remove_callback=remove_callback,
            ),
            "System Init.": SystemInitController(
                properties_controller=properties_controller,
                workspace_controller=workspace_controller,
                mesh_callback=mesh_callback,
                init_mag_callback=init_mag_callback,
            ),
        }

    def build(self) -> widgets.Widget:
        return self._make_tab(self.features)
