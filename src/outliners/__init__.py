#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Project: UbermagGUI

src/outliners/__init__.py:
    Each directory contains an 'Outliner' that `src/builder.py` uses when generating the entire
    interface.

    Outliners contain 'features' (groupings of widgets), and each outliner is responsible
    for:
        -
"""

from .scenes.region_lists import RegionListReadOnly

__all__ = [
    "RegionListReadOnly",
]
