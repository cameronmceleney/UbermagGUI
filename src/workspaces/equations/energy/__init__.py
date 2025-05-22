#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Project: UbermagGUI

~/equations/energy/__init__.py:
    Let the user enter equations required by `micromagneticmodel.System.energy`.

"""
from src.workspaces.equations.energy.zeeman import StaticZeeman

__all__ = [
    "StaticZeeman"
]
