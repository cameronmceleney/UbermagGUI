#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Project: Ubermag
Path:    include/Uberwidgets/region_designer_interface/type_aliases.py

Description:
    Type aliases to ensure that builder.py ultimately returns the correct types for Ubermag.

Author:      Cameron Aidan McEleney < c.mceleney.1@research.gla.ac.uk >
Created:     01 May 2025
IDE:         PyCharm
Version:     0.1.0
"""
import typing

__all__ = [
    "UbermagDimsType",
    "UbermagUnitsType",
    "UbermagCellsizeType",
    "UNIT_FACTORS"
    ]

UNIT_FACTORS = {'m': 1, 'um': 1e-6, 'nm': 1e-9}
# -------------------------------------------------------------------
# Region attribute aliases
# -------------------------------------------------------------------
# discretisedfield.Region.dims  → UbermagDimsType
UbermagDimsType   = typing.Tuple[str, str, str]

# discretisedfield.Region.units  → UbermagUnitsType
UbermagUnitsType  = typing.Tuple[str, str, str]

# -------------------------------------------------------------------
# Discretisation aliases
# -------------------------------------------------------------------
# discretisedfield.Mesh.cell → UbermagCellsizeType
UbermagCellsizeType = typing.Tuple[float, float, float]