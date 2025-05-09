#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""z
Project: UbermagGUI
Path: ./src/__init__.py

Description:
    Package initialization for Region Designer Interface.
    Exports the main RegionDesigner class from builder.

Author:      Cameron Aidan McEleney < c.mceleney.1@research.gla.ac.uk >
Created:     29 Apr 2025
IDE:         PyCharm
Version:     0.1.0
"""

# Standard library imports

# Third-party imports

# Local application imports
from .builder import RegionDesigner

__all__ = ["RegionDesigner"]
