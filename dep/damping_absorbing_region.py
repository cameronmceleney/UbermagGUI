import numpy as np
import custom_system_properties as csp
from typing import Callable, List, Tuple
import discretisedfield as df

class AlphaABC:
    """
    Callable class to compute a spatially varying damping (alpha) value.

    The class is initialised with:
      - alpha_bulk: the bulk damping value.
      - alpha_driven: the damping value in the driven region.
      - system_prop: an object (or dict) that contains system properties such as p1, p2, and cell.
      - system_subregions: a container with subregions (e.g. 'driven', 'gradientLhs', 'gradientRhs',
        'dampingLhs', etc.). Each subregion is expected to have a 'region' attribute (supporting
        the "in" operator) and properties p1, p2, and (for dampingLhs) a 'multiplier' and 'edges'.

    Once initialised, an instance can be used as a function: given a position tuple (x, y, z) in
    base units, __call__ returns the appropriate damping value.
    """

    def __init__(self, alpha_bulk: float,
                 alpha_driven: float,
                 system_prop: csp.SystemProperties,
                 system_subregions: csp.MyRegions):

        self.alpha_bulk = alpha_bulk
        self.alpha_driven = alpha_driven
        self.system_prop = system_prop
        self.system_subregions = system_subregions

    def damping_interfacial(self, x_left, x_right, alpha_left, alpha_right, xn):
        """
        Computes a damping value by linearly interpolating between alpha_left and alpha_right.
        The interpolation is performed over a number of cells defined by the parent's cell size.
        """
        cell_size = self.system_prop.cell[0]
        xmin_interfacial = int(x_left / cell_size)
        xmax_interfacial = int(x_right / cell_size)
        num_cells = xmax_interfacial - xmin_interfacial
        if num_cells <= 0:
            raise ValueError("Invalid number of cells for damping interpolation.")
        alpha_linspace = np.linspace(alpha_left, alpha_right, num_cells)
        # Use an integer step calculated from the cell size in nanometers.
        step = int(cell_size / 1e-9)
        pos_indexed = np.arange(xmin_interfacial, xmax_interfacial, step, dtype=int)
        mapping_indices_damping = dict(zip(pos_indexed, alpha_linspace))
        if xn in mapping_indices_damping:
            return mapping_indices_damping[xn]
        else:
            raise ValueError(f"Cell index {xn} not found in damping mapping.")

    def __call__(self, pos):
        """
        Given a position 'pos' (a tuple in base units), return the local damping value.
        """
        # Unpack spatial coordinates in base units.
        x, y, z = pos
        # Convert to cell coordinates in nanometers (assuming 1e9 conversion).
        xn, yn, zn = tuple(coord * 1e9 for coord in pos)

        # First, if the position lies in the 'driven' region, return alpha_driven.
        if xn in self.system_subregions.driven.region:
            return self.alpha_driven

        # Check if the position is in one of the interfacial gradient regions.
        # if xn in self.system_subregions.gradientLhs.region:
        #     return self.damping_interfacial(
        #         self.system_subregions.gradientLhs.p1[0],
        #         self.system_subregions.gradientLhs.p2[0],
        #         self.alpha_bulk, self.alpha_driven, xn
        #     )
        # elif xn in self.system_subregions.gradientRhs.region:
        #     return self.damping_interfacial(
        #         self.system_subregions.gradientRhs.p1[0],
        #         self.system_subregions.gradientRhs.p2[0],
        #         self.alpha_driven, self.alpha_bulk, xn
        #     )

        if xn not in self.system_subregions.dampingLhs.region or xn not in self.system_subregions.dampingRhs.region:
            return self.alpha_bulk

        # Otherwise, the site is in the bulk or in a fixed region.
        # Get system boundary coordinates in nanometers.
        xmin, ymin, zmin = tuple(p * 1e9 for p in self.system_prop.p1)
        xmax, ymax, zmax = tuple(p * 1e9 for p in self.system_prop.p2)

        # For the dampingLhs region, get the widths.
        derived_widths_lhs = [int(val / self.system_subregions.dampingLhs.region.multiplier)
                              for val in self.system_subregions.dampingLhs.region.edges]
        widths = {'x': derived_widths_lhs[0], 'y': derived_widths_lhs[1], 'z': derived_widths_lhs[2]}

        # Define left and right bounds for the A.B.C. region.
        xa = xmin + widths['x']
        xb = xmax - widths['x']

        # Scale damping near the edges.
        if xn < xa:
            return np.exp(((xmin - xn) * np.log(self.alpha_bulk)) / (xmin - xa))
        elif xn > xb:
            return np.exp(((xmax - xn) * np.log(self.alpha_bulk)) / (xmax - xb))

        # In the bulk, return the bulk damping.
        return self.alpha_bulk


class AlphaProfile:
    """Base class: return None if this profile doesn’t apply at pos."""
    def __call__(self, pos):
        raise NotImplementedError


class BulkAlpha(AlphaProfile):
    def __init__(self, alpha_bulk: float):
        self.alpha_bulk = alpha_bulk

    def __call__(self, pos):
        return self.alpha_bulk


class DrivenRegionAlpha(AlphaProfile):
    def __init__(self, region, alpha_driven: float):
        self.region = region
        self.alpha_driven = alpha_driven

    def __call__(self, pos):
        if pos in self.region:
            return self.alpha_driven
        return None


class LinearGradientAlpha(AlphaProfile):
    """
    Interpolate α linearly between alpha_left and alpha_right over region `grad_region`.
    Outside that region returns None.
    """
    def __init__(self, grad_region, p1, p2, alpha_left, alpha_right, cell_size):
        self.region = grad_region
        self.x0, self.x1 = p1, p2
        self.alpha_left = alpha_left
        self.alpha_right = alpha_right
        self.cell = cell_size

    def __call__(self, pos):
        if pos not in self.region:
            return None
        x, *_ = pos
        if x < self.x0 or x > self.x1:
            return None
        # linear ramp
        t = (x - self.x0) / (self.x1 - self.x0)
        return self.alpha_left + t * (self.alpha_right - self.alpha_left)

class ExponentialGradientAlpha(AlphaProfile):
    """
    Exponential interpolation between alpha_start and alpha_end over grad_region.
    alpha(x) = alpha_start * (alpha_end / alpha_start) ** t,
    where t = (x - x0)/(x1 - x0). Returns None outside region.
    """
    def __init__(self,
                 grad_region: df.Region,
                 p1: float,
                 p2: float,
                 alpha_start: float,
                 alpha_end: float):
        self.region      = grad_region
        self.x0, self.x1 = p1, p2
        self.alpha_start = alpha_start
        self.alpha_end   = alpha_end
        # precompute ln(ratio)
        self.log_ratio   = np.log(alpha_end / alpha_start)

    def __call__(self, pos: Tuple[float,float,float]):
        if pos not in self.region:
            return None
        x = pos[0]
        if x < self.x0 or x > self.x1:
            return None
        t = (x - self.x0) / (self.x1 - self.x0)
        return self.alpha_start * np.exp(self.log_ratio * t)


class TanhGradientAlpha(AlphaProfile):
    """
    Smooth tanh‐shaped interpolation between alpha_start and alpha_end over grad_region.
    alpha(x) = alpha_start + (alpha_end - alpha_start)*(1 + tanh(k*(2*t-1)))/2,
    where t = (x - x0)/(x1 - x0). Returns None outside region.
    """
    def __init__(self,
                 grad_region: df.Region,
                 p1: float,
                 p2: float,
                 alpha_start: float,
                 alpha_end: float,
                 steepness: float = 5.0):
        self.region      = grad_region
        self.x0, self.x1 = p1, p2
        self.alpha_start = alpha_start
        self.alpha_end   = alpha_end
        self.k           = steepness
        self.delta       = alpha_end - alpha_start

    def __call__(self, pos: Tuple[float,float,float]):
        if pos not in self.region:
            return None
        x = pos[0]
        if x < self.x0 or x > self.x1:
            return None
        t = (x - self.x0) / (self.x1 - self.x0)
        # tanh argument from -k to +k as x runs across region
        y = np.tanh(self.k * (2*t - 1))
        # map y ∈ [-1,+1] to [0,1]
        s = (1 + y) / 2
        return self.alpha_start + self.delta * s

class AbsorbingLinearAlpha(AlphaProfile):
    """
    Linear ramp between 1.0 (at the region edge nearest free/driven side)
    and alpha_bulk (at depth w).  If reverse=True, swap endpoints.
    """
    def __init__(self,
                 region: df.Region,
                 edge_width: float,
                 alpha_bulk: float,
                 reverse: bool = False):
        self.region     = region
        self.xmin, self.xmax = region.pmin[0], region.pmax[0]
        self.w          = edge_width
        self.alpha_bulk = alpha_bulk
        self.reverse    = reverse

    def __call__(self, pos: Tuple[float,float,float]):
        if pos not in self.region:
            return None
        x = pos[0]

        # left edge
        dL = x - self.xmin
        if dL <= self.w:
            t = dL / self.w
            if not self.reverse:
                return 1.0 - (1.0 - self.alpha_bulk) * t
            else:
                return self.alpha_bulk + (1.0 - self.alpha_bulk) * t

        # right edge
        dR = self.xmax - x
        if dR <= self.w:
            t = dR / self.w
            if not self.reverse:
                return 1.0 - (1.0 - self.alpha_bulk) * t
            else:
                return self.alpha_bulk + (1.0 - self.alpha_bulk) * t

        return None


class AbsorbingExponentialAlpha(AlphaProfile):
    """
    Exponential ramp exp(log(alpha_bulk) * (d/w)) from 1.0→alpha_bulk.
    If reverse=True, exp(log(alpha_bulk) * (1−d/w)) from alpha_bulk→1.0.
    """
    def __init__(self,
                 region: df.Region,
                 edge_width: float,
                 alpha_bulk: float,
                 reverse: bool = False):
        self.region     = region
        self.xmin, self.xmax = region.pmin[0], region.pmax[0]
        self.w          = edge_width
        self.log_bulk   = np.log(alpha_bulk)
        self.reverse    = reverse

    def __call__(self, pos: Tuple[float,float,float]):
        if pos not in self.region:
            return None
        x = pos[0]

        # left edge
        dL = x - self.xmin
        if dL <= self.w:
            frac = dL / self.w
            if not self.reverse:
                return np.exp(self.log_bulk * frac)
            else:
                return np.exp(self.log_bulk * (1 - frac))

        # right edge
        dR = self.xmax - x
        if dR <= self.w:
            frac = dR / self.w
            if not self.reverse:
                return np.exp(self.log_bulk * frac)
            else:
                return np.exp(self.log_bulk * (1 - frac))

        return None


class AbsorbingTanhAlpha(AlphaProfile):
    """
    Smooth tanh ramp between 1.0→alpha_bulk (default) or alpha_bulk→1.0 if reverse=True.
    """
    def __init__(self,
                 region: df.Region,
                 edge_width: float,
                 alpha_bulk: float,
                 steepness: float = 5.0,
                 reverse: bool = False):
        self.region      = region
        self.xmin, self.xmax = region.pmin[0], region.pmax[0]
        self.w           = edge_width
        self.alpha_bulk  = alpha_bulk
        self.k           = steepness
        self.reverse     = reverse

    def __call__(self, pos: Tuple[float,float,float]):
        if pos not in self.region:
            return None
        x = pos[0]

        # define helper to compute tanh‐mix
        def mix(t: float) -> float:
            y = np.tanh(self.k * (2*t - 1))
            if not self.reverse:
                # maps y: -1→+1  to s: 1→0
                s = (1 - y)/2
            else:
                # maps y: -1→+1  to s: 0→1
                s = (1 + y)/2
            return self.alpha_bulk + (1.0 - self.alpha_bulk) * s

        # left edge
        dL = x - self.xmin
        if dL <= self.w:
            return mix(dL / self.w)

        # right edge
        dR = self.xmax - x
        if dR <= self.w:
            return mix(dR / self.w)

        return None


class CompositeAlpha:
    """
    Chains multiple AlphaProfile callables. Returns the first non‐None result;
    otherwise raises or returns a default bulk value.
    """
    def __init__(self,
                 profiles: List[Callable],
                 alpha_bulk: float):
        self.profiles = profiles
        self.alpha_bulk = alpha_bulk

    def __call__(self, pos):
        for p in self.profiles:
            val = p(pos)
            if val is not None:
                return val
        return self.alpha_bulk

#######################
class FieldProfile:
    """Base class: return None if this profile doesn’t apply at pos."""
    def __call__(self, pos):
        raise NotImplementedError


class BulkFieldStrength(FieldProfile):
    def __init__(self, field_strength_bulk: tuple):
        self.field_strength_bulk: tuple = field_strength_bulk

    def __call__(self, pos):
        return self.field_strength_bulk


class UniformFieldStrength(FieldProfile):
    def __init__(self, region, uniform_field_strength: tuple):
        self.region: df.Region = region
        self.uniform_field_strength: tuple = uniform_field_strength

    def __call__(self, pos):
        if pos in self.region:
            return self.uniform_field_strength
        else:
            return None

class LinearGradientField(FieldProfile):
    """
    Interpolate α linearly between field_left and field_right over region `grad_region`.
    Outside that region returns None.
    """
    def __init__(self, grad_region, p1, p2, field_strength_left, field_strength_right, cell_size):
        self.region: df.Region = grad_region
        self.x0, self.x1 = p1, p2
        self.field_strength_left: tuple = field_strength_left
        self.field_strength_right: tuple = field_strength_right
        self.cell: tuple = cell_size

    def __call__(self, pos):
        if pos not in self.region:
            return None
        x, *_ = pos
        if x < self.x0 or x > self.x1:
            return None
        # linear ramp
        t = (x - self.x0) / (self.x1 - self.x0)
        res = (0,
               0,
               self.field_strength_left[2] + t * (self.field_strength_right[2] - self.field_strength_left[2])
               )
        return tuple(res)

class CompositeFieldStrength:
    """
    Chains multiple FieldProfile callables. Returns the first non‐None result;
    otherwise raises or returns a default bulk value.
    """

    def __init__(self,
                 profiles: List[Callable],
                 field_strength_bulk: float):
        self.profiles = profiles
        self.field_strength_bulk = field_strength_bulk

    def __call__(self, pos):
        for p in self.profiles:
            val = p(pos)
            if val is not None:
                return val
        return self.field_strength_bulk
