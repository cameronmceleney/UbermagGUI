#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Project: UbermagGUI

~/equations/dynamics/__init__.py:
    Let the user enter equations required by `micromagneticmodel.System.dynamics`.

"""
from src.workspaces.equations.dynamics.precession import PrecessionTerm

__all__ = [
    "PrecessionTerm"
]
