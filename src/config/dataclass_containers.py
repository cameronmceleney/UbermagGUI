#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Project: UbermagGUI
Path:    src/config/dataclass_containers.py

_CoreProperties:
    Dataclass that holds all global states for the interface. Should be instanced once, and then
    shared via inheritance throughout UbermagInterface.
    
Author:      Cameron Aidan McEleney < c.mceleney.1@research.gla.ac.uk >
Created:     14 May 2025
IDE:         PyCharm
Version:     0.1.0
"""

# Standard library imports
from dataclasses import dataclass, field, InitVar
import logging
from typing import ClassVar

# Third-party imports
import discretisedfield as df
import micromagneticmodel as mm

# Local application imports

__all__ = ["_CoreProperties"]

logger = logging.getLogger(__name__)


@dataclass
class _CoreProperties:
    """
    Holds all global states for the interface in one place.
    """
    # Init-only attribute for inputting micromagnetic System
    initial_system: InitVar[mm.System] = None
    _init_in: bool = field(default=False, init=False, repr=False)

    # Private attribute that stores true System
    _system: mm.System | None = field(init=False, default=None, repr=False)

    # Public containers of named objects
    meshes: dict[str, df.Mesh] = field(default_factory=dict)
    regions: dict[str, df.Region] = field(default_factory=dict)

    # --- Internals (not passed to __init__) ---
    # Name that properties associated with the overall domain refer to
    _domain_key: ClassVar[str] = field(init=False, default='main', repr=False)

    # _cell defaults to 1 unit along each axis; unit set by user at runtime.
    _cell: tuple = field(init=False, default=(1, 1, 1), repr=False)
    _dims: tuple = field(init=False, default=('x', 'y', 'z'), repr=False)
    _units: tuple = field(init=False, default=('m', 'm', 'm'), repr=False)

    def __post_init__(self, initial_system: mm.System):
        """
        If the user loaded initial meshes/regions, feed them through our
        private setters for initialisation.
        """
        self._init_in = True
        if isinstance(initial_system, mm.System):
            self._load_new_system(initial_system)

        for name, mesh in tuple(self.meshes.items()):
            self._add_mesh(name, mesh)

        for name, region in tuple(self.regions.items()):
            self._add_region(name, region)

    def __repr__(self):
        """Need this method as there is no other way of including ``system`` in the
        ``__repr__``; it is labelled as ``_system``. """
        return (
            f"{self.__class__.__name__}("
            f"system={self._system!r}, "
            f"meshes={self.meshes!r}, "
            f"regions={self.regions!r})"
        )

    # --- Public methods to easily read key attributes
    @property
    def main_system(self) -> None | mm.System:
        """Return the currently active System."""
        return self._system

    @main_system.setter
    def main_system(self, new):
        """
        Dummy. Required to prevent ``AppContext`` crashing during ``__init__``.

        Silently updates log if user passes 'new' to highlight they attempted something invalid
        """
        if not self._init_in:
            # self._system is None or isinstance(self._system, mm.System):
            logger.debug(f'User tried to publicly update the system %r', new, stack_info=True)

    @property
    def main_mesh(self) -> df.Mesh:
        """The currently active mesh that all other meshes must be compatible with."""
        return self._main_mesh

    @property
    def main_region(self) -> df.Region:
        """The region underlying the main mesh in which all other regions much be positioned."""
        return self._main_region

    @property
    def cell(self):
        """The cell‐size of the main mesh."""
        if self._domain_key in self.meshes:
            return self.main_mesh.cell

        return self._cell

    @property
    def dims(self):
        """The dimension labels, e.g. 'm', for the system."""
        if self._domain_key in self.regions:
            return self.main_region.dims

        return self._dims

    @property
    def units(self):
        """The units of the system."""
        if self._domain_key in self.regions:
            return self.main_region.units

        return self._units

    # --- private methods for controlled mutation of main attributes and their derivatives ---
    @property
    def _main_mesh(self):
        if self._domain_key in self.meshes:
            return self.meshes[self._domain_key]

        return None

    @_main_mesh.setter
    def _main_mesh(self, mesh: df.Mesh):
        """
        Push ``mesh`` to being the active mesh for the entire system, and update all derived states.

        The ``dims`` and ``units`` for the entire system are derived from ``mesh``.
        """
        # Error handling in ``self._add_mesh`` ensures valid typings
        self.meshes[self._domain_key] = mesh

        # Make mesh's region our main region, and update all derived states
        self._main_region = mesh.region
        self._add_mesh_subregions(mesh)

    @property
    def _main_region(self):
        if self._domain_key in self.regions:
            return self.regions[self._domain_key]

        return None

    @_main_region.setter
    def _main_region(self, region: df.Region):
        """Let the user push the current main region onto the region's container."""
        # Error handling in ``self._add_region`` ensures valid typings
        logger.debug("CoreProperties._main_region.setter: setting main_region -> %r", region)
        self._add_region(self._domain_key, region)

        # If region was valid then we're guaranteed correct types
        self._dims = self.regions[self._domain_key].dims
        self._units = self.regions[self._domain_key].units

    # TODO. Consider if these private methods should be removed from dataclass, and added to Controllers
    # --- private methods for addition/removal to dictionaries
    def _add_mesh(self, name: str, mesh: df.Mesh):
        """Insert a named mesh to ``meshes`` and optionally make it currently active."""

        if not isinstance(mesh, df.Mesh):
            logger.error("Attempted to add non-Mesh %r under name %r", mesh, name, stack_info=True)
        self.meshes[name] = mesh

    def _remove_mesh(self, name: str):
        """Drop a mesh from ``meshes``."""
        if name in self.meshes.keys():
            self.meshes.pop(name, None)
        else:
            logger.debug("Requested mesh %r for removal not in meshes %r", name, self.meshes, stack_info=True)

    def _add_mesh_subregions(self, mesh: df.Mesh):
        """Add any subregions inside the mesh to our main region container"""
        for subregion_name, region in mesh.subregions.items():
            self._add_region(subregion_name, region)

    def _add_region(self, name: str, region: df.Region):
        """Insert a named region into ``_CoreProperties.regions``."""
        logger.debug("CoreProperties._add_region: storing regions[%r] = %r", name, region)
        if not isinstance(region, df.Region):
            logger.error("Attempted to add non-Region %r under name %r", region, name, stack_info=True)

        self.regions[name] = region

    def _remove_region(self, name: str):
        if name in self.regions.keys():
            self.regions.pop(name, None)
        else:
            logger.debug("Requested region %r for removal not in regions %r", name, self.regions, stack_info=True)

    def _load_new_system(self, new: mm.System):
        """Advanced users: private, correct way to push in new System, and reload the class' attributes."""
        if not isinstance(new, mm.System):
            raise TypeError(f"Expected mm.System, got {type(new)}")
        self._system = new
        self._reload_system()

    def _reload_system(self):
        """Takes the currently active system, and updates class' properties. Only for internal use."""
        if self._system.m:
            self.meshes.clear()
            self.regions.clear()

            mesh = self._system.m.mesh
            self._main_mesh = mesh
            self._main_region = mesh.region
            self.regions["main"] = mesh.region

        if self._system.energy:
            pass

    def _set_initial_magnetisation(self, m0: df.Field):
        """
        Safely update the system’s initial magnetisation.
        """
        if self._system is None:
            raise RuntimeError("No System has been loaded yet")

        self._system.m = m0
        logger.debug("CoreProperties: set initial magnetisation → %r", m0)
