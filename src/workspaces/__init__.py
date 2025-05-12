#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Project: UbermagGUI

src/workspaces/__init__.py:
    Each directory contains a 'workspace' that `src/builder.py` uses to generate the entire
    interface.

    Workspaces contain 'features' (groupings of widgets), and each workspace is responsible
    for:
        - controlling how transitions occur between its features;
        - interfacing with `builder.py` for its systemwide, global variables
        - setting the layout of each feature
"""

from .initialisation.controllers import GeometryController, SystemInitController

__all__ = [
    "GeometryController",
    "SystemInitController"
]
