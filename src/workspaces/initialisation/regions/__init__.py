#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Project: UbermagGUI

initialisation/regions/__init__.py
    Panels which can be used to create, remove, and edit discretisedfieldRegion instances.

"""
from .append import AppendRegionUsingBase
# from .divide import DivideRegion
from .place import PlaceRegion
from .remove import RemoveRegion

__all__ = [
    "AppendRegionUsingBase",
    # "DividePanel",
    "PlaceRegion",
    "RemoveRegion",
]
