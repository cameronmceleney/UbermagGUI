#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Project: UbermagGUI

workspaces/initialisation/__init__.py:
    Import all the panels and controllers required to build this feature-grouping.

    The 'Initialisation' workspace allows the user to create:
        - regions
        - subregions
        - meshes

    This workspace also allows the user to create the domain by defining:
        - the containing region that the entire system lies within;
        - the mesh which discretises this region, and which all other meshes which be
          compatible with;
        - subregions that are present across all meshes; and
        - the state of the initial magnetic field across the domain.
"""
# Features
from src.workspaces.initialisation.controllers import InitialisationGroupFeatureController

# Panels
import src.workspaces.initialisation.domain
import src.workspaces.initialisation.fields
import src.workspaces.initialisation.meshes
import src.workspaces.initialisation.regions

__all__ = [
    "InitialisationGroupFeatureController",
    "domain",
    "fields",
    "regions",
    "meshes",
]
