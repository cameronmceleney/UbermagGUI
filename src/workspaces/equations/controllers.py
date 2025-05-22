#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Project: UbermagGUI
Path:    src/workspaces/equations/controllers.py

EquationsGroupFeatureController:
    Top‐level Feature exposing two sub‐features: Energy & Dynamics.
    
Author:      Cameron Aidan McEleney < c.mceleney.1@research.gla.ac.uk >
Created:     22 May 2025
IDE:         PyCharm
Version:     0.1.0
"""

# Standard library imports
import ipywidgets as widgets

# Third-party imports

# Local application imports
from src.workspaces.utils.feature_base import SingleFeatureController, GroupFeatureController
from . import energy, dynamics

__all__ = [
    "EnergyFeatureController",
    "DynamicsFeatureController",
    "EquationsGroupFeatureController"
]


class EnergyFeatureController(SingleFeatureController):
    def __init__(
            self,
            properties_controller,
            workspace_controller,
            energy_callback,
    ):
        super().__init__(properties_controller)

        # All panels in feature
        self.panels = {
            'Static Zeeman': energy.StaticZeeman(),
        }

        self.panels['Static Zeeman'].set_state_callback(energy_callback)

        # --- subscribe to geometry/mesh changes so dropdowns stay in sync... ---

    def build(self) -> widgets.GridspecLayout:
        return self._build_feature(self.panels)


class DynamicsFeatureController(SingleFeatureController):
    def __init__(
            self,
            properties_controller,
            workspace_controller,
            dynamics_callback
            ):
        super().__init__(properties_controller)

        # panels for each step
        self.panels = {
            'precession': dynamics.PrecessionTerm(),
        }

        self.panels['precession'].set_state_callback(dynamics_callback)

        # --- subscribe to listeners stay in sync with... ---

    def build(self) -> widgets.GridspecLayout:
        return self._build_feature(self.panels)


class EquationsGroupFeatureController(GroupFeatureController):
    """
    Exposes Geometry + System‐Init features under one Tab widget.
    """
    def __init__(
            self,
            # access to top-level shared attributes
            properties_controller,
            workspace_controller,
            # callbacks from top‐level WorkspaceController:
            energy_callback,
            dynamics_callback,
    ):
        # instantiate each feature; wired handled by feature's controller
        self.features = {
            'Energy': EnergyFeatureController(
                properties_controller=properties_controller,
                workspace_controller=workspace_controller,
                energy_callback=energy_callback,
            ),
            'Dynamics': DynamicsFeatureController(
                properties_controller=properties_controller,
                workspace_controller=workspace_controller,
                dynamics_callback=dynamics_callback,
            )
        }

    def build(self) -> widgets.Widget:
        return self._make_tab(self.features)
