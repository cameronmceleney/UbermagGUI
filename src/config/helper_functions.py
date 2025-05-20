#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Project: UbermagGUI
Path:    src/helper_functions.py

Description:
    Short description of what this (helper_functions.py) does.
    
Author:      Cameron Aidan McEleney < c.mceleney.1@research.gla.ac.uk >
Created:     01 May 2025
IDE:         PyCharm
Version:     0.1.0
"""

# Standard library imports

# Third-party imports
from pint import UnitRegistry

# Local application imports

__all__ = [
    "units_to_meter_factors",
    ]

# create a (singleton) registry
_ureg = UnitRegistry()


def units_to_meter_factors(units: tuple[str, str, str]):
    """
    Given a tuple/list of unit strings, return a tuple of floats,
    each equal to how many meters 1 of that unit represents.

    Example:
        >>> units_to_meter_factors(("m","um","nm"))
        (1.0, 1e-6, 1e-9)
    """
    factors = []
    for u in units:
        try:
            # parse “1 u” and convert to meters
            f = (_ureg.Quantity(1, u).to(_ureg.meter)).magnitude
        except Exception:
            raise ValueError(f"Unknown or unsupported unit: {u!r}")
        factors.append(f)
    return tuple(factors)
