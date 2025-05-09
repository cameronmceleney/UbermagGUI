# -*- coding: utf-8 -*-

# -------------------------- Preprocessing Directives -------------------------

# Standard Libraries
import logging as lg
import typing
from sys import exit

# 3rd Party packages
from datetime import datetime
from dataclasses import dataclass, field
from typing import Union, Sequence, Tuple, Dict

# Ubermag modules
import discretisedfield as df
import numpy as np

# ----------------------------- Program Information ----------------------------

"""
I've found that Ubermag handles `Regions` and `Mesh` objects (in `discretisedfield` module) in ways that are opaque, and
this leads to repetition of code. The contents of this file aim to create Handlers and Factories for my system
configuration data, which can then be passed to the relevant Ubermag modules; creating a high-level interface and 
manager.
"""
PROGRAM_NAME = "custom_system_properties.py"
"""
Created on 23 May 24 by Cameron Aidan McEleney
"""


# ---------------------------- Function Declarations ---------------------------

def loggingSetup():
    """
    Minimum Working Example (MWE) for logging. Pre-defined levels are:
        
        Highest               ---->            Lowest
        CRITICAL, ERROR, WARNING, INFO, DEBUG, NOTSET
    """
    today_date = datetime.now().strftime("%y%m%d")
    current_time = datetime.now().strftime("%H%M")

    lg.basicConfig(filename=f'./{today_date}-{current_time}.log',
                   filemode='w',
                   level=lg.INFO,
                   format='%(asctime)s | %(module)s::%(funcName)s | %(levelname)s | %(message)s',
                   datefmt='%Y-%m-%d %H:%M:%S',
                   force=True)


# ------------------------------ Implementations ------------------------------


@dataclass
class SystemProperties:
    """ Class to store the properties of the system being simulated.

    Args:
    @param length: Length of the system, commonly the x-axis (called `lx`)
    @param width: Width of the system, commonly the y-axis (called `ly`)
    @param thickness: Thickness of the system, commonly the z-axis (called `lz`)
    @param cell: Tuple of the cell sizes in the x, y, and z directions often given as (dx, dy, dz)
    """
    length: float
    width: float
    thickness: float
    cell: tuple = field(default_factory=lambda: (0e-9, 0e-9, 0e-9))
    p1: tuple = field(default_factory=lambda: (0, 0, 0))
    units: tuple = field(default=('m', 'm', 'm'))
    p2: tuple = field(init=False)
    numcells: tuple = field(init=False)

    def __post_init__(self):
        if len(self.cell) == 3 and all(c > 0 for c in self.cell):
            self.update_lengths()
        self.p2 = (self.length, self.width, self.thickness)

    def update_lengths(self):
        if len(self.cell) == 3 and all(c > 0 for c in self.cell):
            self.length *= self.cell[0]
            self.width *= self.cell[1]
            self.thickness *= self.cell[2]

            self.p2 = (self.length, self.width, self.thickness)
        else:
            raise ValueError("Cell must be a tuple of three non-zero values")

    def update_numcells(self):
        if len(self.cell) == 3 and all(c > 0 for c in self.cell):
            self.numcells = (int(np.ceil(self.length / self.cell[0])),
                             int(np.ceil(self.width / self.cell[1])),
                             int(np.ceil(self.thickness / self.cell[2])))
        else:
            raise ValueError("Cell must be a tuple of three non-zero values")


@dataclass
class SubRegion:
    name: str = 'DefaultSubRegion'
    p1: tuple[int | float] = field(default=None)
    p2: tuple[int | float] = field(default=None)

    _cellsize: tuple[int | float] = field(default_factory=tuple)
    _dims: tuple[int] = field(default_factory=tuple)
    _dim_labels: tuple[str] = field(default_factory=tuple)
    _units: tuple[str] = field(default_factory=tuple)

    _region: df.Region = field(init=False, default=None)
    _mesh: df.Mesh = field(init=False, default=None)

    def __post_init__(self):
        self._pmin = self.p1
        self._pmax = self.p2
        self._name = self.name

        self.create_region()

    def __call__(self, **kwargs):
        # Default options for if no kwargs are passed (ideally want to return the region)
        if kwargs:
            self.set_values(**kwargs)
            self.create_region()

        if self.region is not None:
            return self.region
        else:
            self.__repr__()

    def __str__(self) -> str:
        return f'Subregion: {self.name}'

    def __repr__(self):
        """
        Return a string representation of the object.

        Due to how Ubermag handles regions, this is actually performing
        `self.region.__repr__() actually` returns `html.strip_tags(self._repr_html_())`
        """
        # Default options for if no kwargs are passed (ideally want to return the region)
        return (f'p1: {self._pmin}, '
                f'p2: {self._pmax}, '
                f'cell: {self._cellsize}, '
                f'dims: {self._dims}, '
                f'dim. labels: {self._dim_labels}, '
                f'units: {self._units}')

    @property
    def name(self) -> str:
        return self._name

    @name.setter
    def name(self, value: str):
        self._name = value

    @property
    def pmin(self) -> tuple:
        return self._pmin

    @property
    def pmax(self) -> tuple:
        return self._pmax

    @property
    def dims(self) -> tuple:
        return self._dims

    @dims.setter
    def dims(self, value: tuple):
        if isinstance(value, tuple) and len(value) == 3:
            self._dims = value
        else:
            raise ValueError("Dimensions must be a tuple of three values")

    @property
    def dim_labels(self) -> tuple:
        return self._dim_labels

    @dim_labels.setter
    def dim_labels(self, value: tuple):
        if isinstance(value, tuple) and len(value) == 3:
            self._dim_labels = value
        else:
            raise ValueError("Dimensions must be a tuple of three values")

    @property
    def units(self) -> tuple:
        return self._units

    @units.setter
    def units(self, value: tuple):
        if isinstance(value, tuple) and len(value) == 3:
            self._units = value
        else:
            raise ValueError("Units must be a tuple of three values")

    @property
    def cell(self) -> tuple:
        return self._cellsize

    @cell.setter
    def cell(self, value: tuple):
        if not (isinstance(value, tuple) and len(value) == 3):
            raise ValueError("Cell size must be a tuple of three values")

        self._cellsize = value

    def set_values(self, **kwargs):
        """
        Update SubRegion's parameters based on the provided keyword arguments.
        :param kwargs:
        :return:
        """
        # Assign positions (p) that are required to draw a cuboid
        if 'p1' in kwargs:
            self._pmin = kwargs['p1']

        if 'p2' in kwargs:
            self._pmax = kwargs['p2']

        if 'cell' in kwargs and kwargs['cell'] is not None:
            self.cell = kwargs['cell']

        if 'units' in kwargs and kwargs['units'] is not None:
            self.units = kwargs['units']

        if 'sizes' in kwargs and kwargs['sizes'] is not None:
            self.dims = kwargs['sizes']

        if 'dims' in kwargs and kwargs['dims'] is not None:
            self.dim_labels = kwargs['dims']

    @property
    def region(self):
        return self._region

    @region.setter
    def region(self, value):
        if isinstance(value, df.Region):
            self._region = value
        else:
            raise ValueError("Region must be an instance of df.Region")

    def create(self):
        """Legacy code for creating the region."""
        self.create_region()

    def create_region(self):
        """
        Create the underlying Region object if pmin and pmax are valid.
        """
        if self.dims and self.cell:
            if self.pmin and not self.pmax:
                self._pmax = tuple(start + c * d for start, d, c in zip(self.pmin, self.dims, self.cell))
            elif self.pmax and not self.pmin:
                self._pmin = tuple(end - c * d for end, d, c in zip(self.pmax, self.dims, self.cell))

        if self.pmin and self.pmax:
            if not all(np.asarray(self.pmin) < np.asarray(self.pmax)):
                raise ValueError(
                    f"The values in {self.pmin=} must be element-wise smaller than in"
                    f" {self.pmax=}; use p1 and p2 if the input values are unordered."
                )

            if len(self.pmin) != len(self.pmax):
                raise ValueError(
                    f"The values in {self.pmin=} and {self.pmax=} must be the same length."
                )

            self.region = df.Region(p1=self.pmin, p2=self.pmax)

            if self.units:
                self._region.units = self.units
            else:
                self.units = self._region.units

            if self.dim_labels:
                self._region.dims = self.dim_labels
            else:
                self.dim_labels = self._region.dims


class MyRegions:
    def __init__(self, name: str):
        self.name = name
        self._details: Dict[str, SubRegion] = {}
        self._mesh: None | df.Mesh = field(init=False, default=None)

    def __getattr__(self, region_name: str):

        # Ignore names starting with underscore (internal attributes)
        if region_name.startswith("_"):
            raise AttributeError(f"'{self.__class__.__name__}' object has no attribute '{region_name}'")

        if region_name == self.name:
            return self.name

        if region_name == '_details':
            print('Naughty - you shouldn\'t be using this!')
            return self.__repr__

        # If the region doesn't exist yet, create a new SubRegion and store it.
        if region_name not in self._details:
            new_sub = SubRegion(name=region_name)
            self._details[region_name] = new_sub
        return self._details[region_name]

    def __repr__(self):
        # Build a multi-line representation:
        # Header: MyRegions: <name>
        # Then each user-defined subregion is printed on its own numbered line.
        keys = [key for key in self._details.keys() if key not in ("shape", "__len__")]
        lines = [f"MyRegions: {self.name}", "Subregions:"]
        for i, key in enumerate(keys, start=1):
            subregion = self._details[key]
            lines.append(f"  {i}. {key}: {repr(subregion)}")
        return "\n".join(lines)

    def __str__(self):
        # For this example, use the same output as __repr__
        return self.__repr__()

    @property
    def mesh(self) -> None | df.Mesh:
        return self._mesh

    @mesh.setter
    def mesh(self, value: df.Mesh):
        if isinstance(value, df.Mesh):
            self._mesh = value
        else:
            raise ValueError("Mesh must be an instance of df.Mesh")

    @property
    def region(self):
        """Legacy."""
        return self.subregions

    @property
    def subregions(self) -> dict[str, df.Region]:
        # Dynamically create a dict of initialized regions
        return {name: subregion.region for name, subregion in self._details.items() if subregion.region is not None}

    @property
    def mag_vals(self):
        # Dynamically create a dict of initialized regions
        return {name: (0, 0, 1) for name, subregion in self._details.items() if subregion.region is not None}

    def add_subregion(self, new_subregion: SubRegion):
        # Allow assignment of a single SubRegion; you could extend this to support iterables.
        if not isinstance(new_subregion, SubRegion):
            raise TypeError(f"Expected a SubRegion instance, got {type(new_subregion)}")
        if new_subregion.name in self._details:
            raise KeyError(f"Subregion '{new_subregion.name}' already exists")
        self._details[new_subregion.name] = new_subregion

    def delete_subregion(self, region_name: str):
        if region_name in self._details:
            del self._details[region_name]
        else:
            raise KeyError(f"(Sub)region '{region_name}' does not exist")

    def append_subregion(self, region_name: str, region: SubRegion):
        if not isinstance(region, SubRegion):
            raise TypeError(f"Expected a SubRegion object, got {type(region)}")
        if region_name in self._details:
            raise KeyError(f"(Sub)region '{region_name}' already exists")
        self._details[region_name] = region

def add_tuples(tuple_a: tuple, tuple_b=None, mult=None, dims=None, base=None):
    if tuple_b is None:
        # Create a tuple of zeros with the same length as tuple1 (to handle 1D/2D/3D cases)
        tuple_b = (0,) * len(tuple_a)

    if mult is not None and isinstance(mult, (float, int)):
        tuple_b = tuple(val * mult for val in tuple_b)

    # Get indexes of dims to be summed, else default to all dims
    dim_to_index = {'x': 0, 'X': 0, 'y': 1, 'Y': 1, 'z': 2, 'Z': 2}
    dims_idxs = [dim_to_index[dim] for dim in dims] if dims is not None else range(len(tuple_a))

    result = list(base if base is not None else tuple_a)

    for i in dims_idxs:
        if i < len(tuple_a):
            result[i] = tuple_a[i] + tuple_b[i]

    for i in range(len(tuple_a)):
        result[i] = np.around(result[i], 9)

    return tuple(result)


def merge_regions(region1: MyRegions, region2: MyRegions) -> MyRegions:
    """
    Merge two MyRegions objects into a new MyRegions object.
    """
    merged = MyRegions(name=f"{region1.name}_merged")
    merged._details = {}

    for key, subregion in region1._details.items():
        merged._details[key] = subregion  # subregion is a SubRegion instance

    # Merge subregions from region2
    for key, subregion in region2._details.items():
        if key in merged._details:
            print(f"Warning: Subregion '{key}' already exists in merged regions; skipping duplicate.")
        else:
            merged._details[key] = subregion

    # Optionally, choose a mesh for the merged regions (here, we take region1's mesh if available)
    merged._mesh = region1._mesh if region1._mesh is not None else region2._mesh

    return merged

def subdivide_region_new(
    mesh: df.Mesh,
    region: df.Region,
    value_min: float,
    value_max: float,
    n_subdivisions: int = None,
    partition_distances: Sequence[float] = None,
    axis: str = 'x',
    name_root: str = 'sub',
    remove_parent: bool = True,
    discretisation_tol: float = 1e-6
) -> Tuple[df.Mesh, Dict[str, float]]:
    """
    Subdivide a parent region in `mesh` into smaller subregions along `axis`,
    interpolate values between `value_min` and `value_max` across them,
    and return a new mesh with these subregions replacing (or augmenting) the parent.

    Parameters
    ----------
    mesh : df.Mesh
        The original mesh containing the parent region as a subregion.
    region : df.Region
        The region to subdivide. Must be one of mesh.subregions.values().
    value_min : float
        Interpolation value at start of region.
    value_max : float
        Interpolation value at end of region.
    n_subdivisions : int, optional
        Number of equal-length subregions to create.
    partition_distances : sequence of float, optional
        Offsets from region.pmin along chosen axis for boundaries (in metres).
    axis : {'x','y','z'}
        Axis along which to subdivide.
    name_root : str, default 'sub'
        Prefix for new subregion names.
    remove_parent : bool, default True
        If True, the original parent region is removed from the mesh.
    discretisation_tol : float, default 1e-6
        Tolerance for checking that subregion lengths align to mesh.cell.

    Returns
    -------
    new_mesh : df.Mesh
        Mesh with updated subregions dict.
    value_dict : dict
        Mapping from new subregion names to interpolated values.
    """
    # map axis to index
    axis_idx = {'x':0, 'y':1, 'z':2}
    if axis not in axis_idx:
        raise ValueError(f"Unknown axis '{axis}'")
    idx = axis_idx[axis]

    # fetch parent boundaries
    pmin = list(region.pmin)
    pmax = list(region.pmax)
    length = pmax[idx] - pmin[idx]

    # determine boundaries
    if partition_distances is not None:
        ds = np.array(partition_distances, dtype=float)
        if np.any(ds < 0) or np.any(ds > length):
            raise ValueError("partition_distances out of range")
        boundaries = np.concatenate(([0.0], ds, [length]))
    elif n_subdivisions is not None:
        boundaries = np.linspace(0.0, length, n_subdivisions+1)
    else:
        raise ValueError("Either n_subdivisions or partition_distances must be set")

    # interpolation values
    N = len(boundaries) - 1
    interp = np.linspace(value_min, value_max, N)

    # ensure mesh.cell aligns if needed
    cell = mesh.cell[idx]

    # collect existing subregions
    # assume mesh.subregions is dict-like mapping names to Region
    orig_subs = {
        name: r for name, r in getattr(mesh, 'subregions', {}).items()
    }
    # if list, convert to generic names
    if not orig_subs:
        orig_list = list(getattr(mesh, 'subregions', []) )
        orig_subs = {f'reg_{i}': r for i,r in enumerate(orig_list)}

    # build new subregion dict
    new_subs = dict(orig_subs)
    if remove_parent:
        # find key(s) matching the parent region and remove
        to_remove = [k for k,v in new_subs.items() if v == region]
        for k in to_remove:
            new_subs.pop(k)

    # create subdivisions
    value_dict = {}
    for i in range(N):
        d0 = boundaries[i]
        d1 = boundaries[i+1]
        p1 = pmin.copy()
        p2 = pmax.copy()
        p1[idx] = round(pmin[idx] + d0, 9)
        p2[idx] = round(pmin[idx] + d1, 9)
        # discretisation check
        if abs(((p2[idx] - p1[idx]) / cell) - round((p2[idx] - p1[idx]) / cell)) > discretisation_tol:
            raise ValueError(f"Subregion length {(p2[idx]-p1[idx])} not multiple of cell {cell}")
        name = f"{name_root}_{i}"
        sub = df.Region(p1=tuple(p1), p2=tuple(p2))
        new_subs[name] = sub
        value_dict[name] = float(interp[i])

    # build new mesh
    new_mesh = df.Mesh(region=mesh.region,
                       cell=mesh.cell,
                       subregions=new_subs)
    return new_mesh, value_dict

def subdivide_region(regions: MyRegions,
                     main_region: SubRegion,
                     value_min, value_max,
                     compatible_discretisation: bool,
                     parent_name: str = None,
                     subregion_name_root: str = None,
                     n_subdivisions: int = None,
                     partition_distances: list = None,
                     axis: str = 'x',
                     remove_parent: bool = True,
                     parent_key: str = "main",
                     discretisation_tol: float = 1e-6):
    """
    Parameters
    ----------
    regions : csp.MyRegions
        The container holding subregions.
    main_region : csp.SubRegion
        The parent region to subdivide.
    value_min : float
        The minimum value for interpolation.
    value_max : float
        The maximum value for interpolation.
    compatible_discretisation : bool
        If True and main_region has a valid cell attribute, then each subregion must
        have a length along the chosen axis that is an integer multiple of the cell size.
    parent_name : str, optional
        Base name to use for the new subregions. Defaults to main_region.name.
    subregion_name_root : str, optional
        Root name for the new subregions. Defaults to parent_name + "_sub".
    n_subdivisions : int, optional
        Number of evenly spaced subregions to create.
    partition_distances : list, optional
        A list or array of distances (from main_region.pmin along the axis) defining the partition boundaries.
        Must be increasing and lie within the span of the region.
    axis : str, default 'x'
        The axis along which to subdivide ('x', 'y', or 'z').
    remove_parent : bool, default True
        Whether to remove the parent region (with key parent_key) from the container.
    parent_key : str, default "main"
        The key corresponding to the parent region in the container.
    discretisation_tol : float, default 1e-6
        Tolerance for checking discretisation compatibility.

    Returns
    -------
    tuple
        A tuple containing:
          - A dict mapping subregion names to the computed value.
          - The updated MyRegions instance.

    Raises
    ------
    ValueError
        If neither n_subdivisions nor partition_distances is provided,
        if partition_distances is invalid, or if a subregion is not discretisable when required.
    """
    # Determine axis index
    axis_to_index = {'x': 0, 'y': 1, 'z': 2}
    if axis not in axis_to_index:
        raise ValueError(f"Axis must be one of {list(axis_to_index.keys())}")
    idx = axis_to_index[axis]

    # Get the parent region boundaries (as numpy arrays)
    parent_pmin = np.array(main_region.pmin)
    parent_pmax = np.array(main_region.pmax)
    parent_length = parent_pmax[idx] - parent_pmin[idx]

    # Get the parent's name
    if parent_name is None:
        parent_name = main_region.name
    if subregion_name_root is None:
        subregion_name_root = parent_name + "_sub"

    # Determine boundaries: either even spacing or from provided distances.
    if partition_distances is not None:
        partition_distances = np.array(partition_distances)
        if partition_distances.ndim != 1:
            raise ValueError("partition_distances must be one-dimensional")
        if np.any(partition_distances < 0) or np.any(partition_distances > parent_length):
            raise ValueError("All partition distances must be between 0 and the length of the parent region along the axis")
        # Build boundaries: starting at 0, then the provided distances, ending with parent_length.
        boundaries = np.concatenate(([0], partition_distances, [parent_length]))
    elif n_subdivisions is not None:
        boundaries = np.linspace(0, parent_length, n_subdivisions + 1)
    else:
        raise ValueError("Either n_subdivisions or partition_distances must be provided")

    # Dictionary to store the interpolated value for each new subregion.
    value_dict = {}
    total = len(boundaries) - 1  # number of subregions

    # Compute the interpolated value.
    interp_values = np.linspace(value_min, value_max, total)
    rnd_precision = 10  # Round to nanometre precision

    # Check if parent's cell is available.
    cell_available = hasattr(main_region, "cell") and main_region.cell not in (None, ()) and sum(main_region.cell) > 0
    if cell_available:
        parent_cell = np.array(main_region.cell)

    # Loop over each subdivision to create a new SubRegion.
    for i in range(total):
        new_pmin = parent_pmin.copy()
        new_pmax = parent_pmax.copy()

        # Set the new boundaries along the chosen axis.
        new_pmin[idx] = round(parent_pmin[idx] + boundaries[i], rnd_precision)
        new_pmax[idx] = round(parent_pmin[idx] + boundaries[i+1], rnd_precision)

        # If compatible_discretisation is required and parent's cell is available,
        # check that the new subregion's length along the axis is an integer multiple of the cell size.
        if compatible_discretisation and cell_available:
            new_length = new_pmax[idx] - new_pmin[idx]
            cell_size = parent_cell[idx]
            ratio = new_length / cell_size
            if not np.isclose(ratio, round(ratio), atol=discretisation_tol):
                raise ValueError(f"Subregion {subregion_name_root}_{i} length ({new_length}) along axis {axis} "
                                 f"is not discretisable by cell size {cell_size}")

        # Create new SubRegion with these boundaries.
        subregion_name = f"{subregion_name_root}{i}"
        new_subregion = SubRegion(name=subregion_name, p1=tuple(new_pmin), p2=tuple(new_pmax))
        regions.add_subregion(new_subregion)

        value_dict[subregion_name] = round(interp_values[i], 4)

    # Optionally, remove the parent region.
    if remove_parent:
        regions.delete_subregion(parent_key)

    return value_dict, regions


def add_inter_subregion_values(*dicts,
                               dmi_chain_left: float,
                               dmi_chain_right: float,
                               precision: int = 10) -> dict:
    """
    Merge the given dicts (ordered), then insert both directions of inter-subregion DMI
    as the arithmetic mean, *without* overly coarse rounding.

    Returns a dict suitable for passing to mm.DMI(D=...).
    """

    # 1) Merge input dicts in order
    merged = {}
    for d in dicts:
        merged.update(d)
    keys = list(merged.keys())
    if not keys:
        return {}

    new_dict = {}

    # 2) End caps: both directions with chain
    first, last = keys[0], keys[-1]
    new_dict[f"entire:{first}"] = dmi_chain_left
    new_dict[f"{first}:entire"] = dmi_chain_left

    # 3) Walk through each key → next_key
    for a, b in zip(keys, keys[1:]):
        # original self‐coupling
        new_dict[a] = merged[a]

        # inter‐face mean, both directions
        avg = (merged[a] + merged[b]) / 2.0
        # only round to a precision that preserves your 1e‑5 scale
        avg = round(avg, precision)
        new_dict[f"{a}:{b}"] = avg
        new_dict[f"{b}:{a}"] = avg

    # 4) last region self‐coupling + right chain
    new_dict[last] = merged[last]
    new_dict[f"{last}:entire"] = dmi_chain_right
    new_dict[f"entire:{last}"] = dmi_chain_right

    return new_dict

@dataclass
class EnergyTerm:
    name: typing.Optional[str] = field(init=True, default="Unnamed EnergyTerm")
    x: int | float = field(init=True, default=None)
    y: int | float = field(init=True, default=None)
    z: int | float = field(init=True, default=None)
    _tuple: tuple = field(init=False)

    def __post_init__(self):
        if self.x is None:
            self.x = 0.0
        if self.y is None:
            self.y = 0.0
        if self.z is None:
            self.z = 0.0

        self._tuple = (self.x, self.y, self.z)

    def __call__(self):
        return self._tuple

    def __repr__(self):
        return f"EnergyTerm: {self.name} ({self.x}, {self.y}, {self.z})"

    def __str__(self):
        if self.name is not None:
            return self.name
        else:
            raise ValueError("Name is not set for this energy term.")
