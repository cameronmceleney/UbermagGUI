#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Project: UbermagGUI

~/workspaces/equations/__init__.py:
    Import all the panels and controllers required to build this feature-grouping.

"""
# Features
from src.workspaces.equations.controllers import EquationsController

# Panels
import src.workspaces.equations.energy
import src.workspaces.equations.dynamics

__all__ = [
    "EquationsController",
    "energy",
    "dynamics"
    ""
]
