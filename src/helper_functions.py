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
from discretisedfield import Region
import ipywidgets as widgets
from pint import UnitRegistry

# Local application imports

__all__ = [
    "create_scaled_region_from_base_region",
    "units_to_meter_factors",
    "build_widget_input_values_xyz_tuple"
    ]

# create a (singleton) registry
_ureg = UnitRegistry()


def build_widget_input_values_xyz_tuple(label_tex, default) -> widgets.HBox:
    _textbox_width: str = "3em"

    # x-axis value
    txt_x = widgets.FloatText(
        value=str(default[0]),
        layout=widgets.Layout(width=_textbox_width, flex="0 0 auto")
    )

    # y-axis value
    txt_y = widgets.FloatText(
        value=str(default[1]),
        layout=widgets.Layout(width=_textbox_width, flex="0 0 auto")
    )

    # x-axis value
    txt_z = widgets.FloatText(
        value=str(default[2]),
        layout=widgets.Layout(width=_textbox_width, flex="0 0 auto")
    )

    # Display to user
    html_box_label = widgets.HTMLMath(
        label_tex,
        layout=widgets.Layout(width="auto", flex="0 0 auto")
    )

    hbox_to_output = widgets.HBox(
        [html_box_label, txt_x, txt_y, txt_z],
        layout=widgets.Layout(
            align_items="center",
            align_content="center",
            justify_content='flex-end',
            gap="4px",
        )
    )

    return hbox_to_output


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


def create_scaled_region_from_base_region(
        base_region: Region,
        scale_amount: float,
        cellsize: tuple,
        reference_side: str = 'max',
        scale_along_axis: str = 'x',
        scale_is_absolute: bool = False
) -> Region:

    """
    Create a new Region by slicing off a one-cell slab from base_region along
    the specified axis and end, then scaling that slab.

    Parameters
    ----------
    base_region
        The Region to append off.
    scale_amount
        If scale_is_absolute is False, number of cells to scale by.
        If True, absolute distance in same units as base_region.units.
    cellsize
        Tuple of cell sizes (dx,dy,dz) in same units as base_region.
    reference_side
        Which face of base_region to slice from:
          'max', '+ve', 'positive' → pmax face
          'min', '-ve', 'negative' → pmin face
    scale_along_axis
        One of 'x','y','z'.
    scale_is_absolute
        If True, `scale_amount` is an absolute length. Otherwise it's in cells.

    Returns
    -------
    Region
        The new appended Region.
    """
    # map axis name → index
    axis_map = {'x': 0, 'y': 1, 'z': 2}
    if scale_along_axis not in axis_map:
        raise ValueError(f"Invalid axis: {scale_along_axis!r}, expected one of {list(axis_map)}")
    axis_scale_index = axis_map[scale_along_axis]
    ax = axis_map[scale_along_axis]

    # Choose face to scale along. Various keywords accepted to allow context-specific inputs in calling code.
    keys_scale_rightward = ('max', '+ve', 'positive')
    keys_scale_leftward  = ('min', '-ve', 'negative')

    slab_min = list(base_region.pmin)
    slab_max = list(base_region.pmax)

    ref = reference_side.lower()
    # Slice a 1-cell slab at the positive (negative) face along the chosen axis
    if ref in keys_scale_rightward:
        slab_min[ax] = base_region.pmax[ax]
        slab_max[ax] = base_region.pmax[ax] + cellsize[ax]
    elif ref in keys_scale_leftward:
        slab_min[ax] = base_region.pmin[ax] - cellsize[ax]
        slab_max[ax] = base_region.pmin[ax]
    else:
        raise ValueError(f"Invalid reference_side: {reference_side!r}")

    # Build new slab (region) that we will scale up to the desired size
    slab = Region(
        p1=tuple(slab_min),
        p2=tuple(slab_max),
        dims=base_region.dims,
        units=base_region.units
    )

    # Compute scaling factor along each axis
    scaling_factors = [1.0, 1.0, 1.0]
    if scale_is_absolute:
        factor = round(scale_amount / cellsize[axis_scale_index], cellsize[axis_scale_index])
    else:
        factor = scale_amount

    scaling_factors[axis_scale_index] = factor

    # scale in place=False to get a new Region
    scaled = slab.scale(
        factor=tuple(scaling_factors),
        reference_point=slab.pmin,
        inplace=False
    )

    # round to tidy floats
    new_pmin = tuple(round(v, 9) for v in scaled.pmin)
    new_pmax = tuple(round(v, 9) for v in scaled.pmax)

    return Region(
        p1=new_pmin,
        p2=new_pmax,
        dims=base_region.dims,
        units=base_region.units
    )
