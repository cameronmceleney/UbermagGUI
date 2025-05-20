# region_utils.py

from discretisedfield import Region
from typing import Sequence

__all__ = ["create_scaled_region_from_base_region"]

# module-level constants
_AXIS_INDICES = {"x": 0, "y": 1, "z": 2}
_REF_SIDES = {
    "positive": ("max", "+ve", "positive"),
    "negative": ("min", "-ve", "negative"),
}
_ROUND_PRECISION = 9

def _make_region(p1: Sequence[float], p2: Sequence[float], template: Region) -> Region:
    return Region(
        p1=tuple(round(v, _ROUND_PRECISION) for v in p1),
        p2=tuple(round(v, _ROUND_PRECISION) for v in p2),
        dims=template.dims,
        units=template.units,
    )

def create_scaled_region_from_base_region(
        base_region: Region,
        scale_amount: float,
        cellsize: Sequence[float],
        reference_side: str = 'max',
        scale_along_axis: str = 'x',
        scale_is_absolute: bool = False,
) -> Region:
    """
    See original docstring…
    """
    # 1) look up axis
    try:
        axis_i = _AXIS_INDICES[scale_along_axis]
    except KeyError:
        raise ValueError(f"Invalid axis {scale_along_axis!r}. Choose one of {_AXIS_INDICES}.")

    # 2) decide which face
    ref = reference_side.lower()
    if ref in _REF_SIDES["positive"]:
        face = "positive"
    elif ref in _REF_SIDES["negative"]:
        face = "negative"
    else:
        raise ValueError(f"Invalid reference_side {reference_side!r}")

    # 3) slice off a one-cell slab
    smin, smax = list(base_region.pmin), list(base_region.pmax)
    if face == "positive":
        smin[axis_i] = base_region.pmax[axis_i]
        smax[axis_i] = base_region.pmax[axis_i] + cellsize[axis_i]
    else:
        smin[axis_i] = base_region.pmin[axis_i] - cellsize[axis_i]
        smax[axis_i] = base_region.pmin[axis_i]

    slab = _make_region(smin, smax, base_region)

    # 4) compute scaling factor
    if scale_is_absolute:
        factor = round(scale_amount / cellsize[axis_i], _ROUND_PRECISION)
    else:
        factor = scale_amount

    factors = [1.0, 1.0, 1.0]
    factors[axis_i] = factor

    # 5) scale and return
    scaled = slab.scale(factor=tuple(factors),
                        reference_point=slab.pmin,
                        inplace=False)
    return _make_region(scaled.pmin, scaled.pmax, base_region)