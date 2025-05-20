#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Project: UbermagGUI
Path:    src/workspaces/initialisation/panels/region_utils.py

Description:
    Short description of what this (region_utils.py) does.
    
Author:      Cameron Aidan McEleney < c.mceleney.1@research.gla.ac.uk >
Created:     20 May 2025
IDE:         PyCharm
Version:     0.1.0
"""

# Standard library imports

# Third-party imports
from discretisedfield import Region
from sympy.strategies.core import switch

# Local application imports
from src.config.type_aliases import _AXIS_INDICES

# module-level constants
_ROUND_PRECISION = 9

__all__ = ["create_scaled_region_from_base_region"]


def _make_region(p1: Region.pmin, p2: Region.pmax, template: Region) -> Region:
    """Internal helper to prevent unnecessarily long floats bloating `_CoreProperties` containers."""
    return Region(
        p1=tuple(round(v, _ROUND_PRECISION) for v in p1),
        p2=tuple(round(v, _ROUND_PRECISION) for v in p2),
        dims=template.dims,
        units=template.units,
    )


def create_scaled_region_from_base_region(
        base_region: Region,
        scale_amount: float,
        cell: tuple[float, ...],
        reference_side: str = 'max',
        scale_along_axis: str = 'x',
        is_scale_absolute: bool = False
) -> Region:

    """
    Create a new Region by slicing off a one-cell slab from base_region along
    the specified axis and end, then scaling that slab.

    Parameters
    ----------
    base_region
        The Region to append off.
    scale_amount
        If scale_is_absolute is False, the number of cells to scale by.
        If True, absolute distance is in the same units as base_region.units.
    cell
        Tuple of cell sizes (dx,dy,dz) is in the same units as base_region.
    reference_side
        Which face of base_region to slice from:
          'max', '+ve', 'positive' → pmax face
          'min', '-ve', 'negative' → pmin face
    scale_along_axis
        One of 'x','y','z'.
    is_scale_absolute
        If ``True``, `scale_amount` is an absolute length. Otherwise, it's in cells.

    Returns
    -------
    Region
        The new appended `Region`.
    """
    # Lookup axis to append along
    try:
        axis = _AXIS_INDICES[scale_along_axis]
    except KeyError:
        # TODO. Implement logger.
        raise KeyError(f"Invalid axis {scale_along_axis!r}. Choose one of {_AXIS_INDICES}.")

    # Determine which face to append to
    # Prefer match/case here for trio reasons: scalability; readability; ease-of-use.
    match reference_side.lower():
        case "max" | "+ve" | "positive":
            face = 'positive'
        case "min" | "-ve" | "negative":
            face = 'negative'
        case _:
            raise ValueError(f"Invalid reference_side {reference_side!r}")

    # Slice off one-cell wide 'slab' to act as new base region
    slab_min, slab_max = list(base_region.pmin), list(base_region.pmax)
    if face == "positive":
        slab_min[axis] = base_region.pmax[axis]
        slab_max[axis] = base_region.pmax[axis] + cell[axis]
    else:
        slab_min[axis] = base_region.pmin[axis] - cell[axis]
        slab_max[axis] = base_region.pmin[axis]

    slab = _make_region(slab_min, slab_max, base_region)

    # Compute factor to scale our slab using df.Region methods
    # TODO. Implement scaling using two factors.
    factor = scale_amount if not is_scale_absolute else round(scale_amount / cell[axis], _ROUND_PRECISION)

    scale_factors = 3 * [1.0]
    scale_factors[axis] = factor

    scaled_region = slab.scale(
        factor=tuple(scale_factors),
        reference_point=slab.pmin,
        inplace=False,
    )

    return _make_region(scaled_region.pmin, scaled_region.pmax, base_region)
