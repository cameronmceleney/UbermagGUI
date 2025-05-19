#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Project: UbermagGUI

initialisation/domain/__init__.py
    Panels that control how the user defines several system-wide properties including
        - the single region that is used to define the container for the entire system

    Separated these files from their, perhaps, more natural homes like `initialisation/regions`
    to highlight their functionality.

"""

from .define import DefineDomainRegion

__all__ = [
    "DefineDomainRegion"
]
