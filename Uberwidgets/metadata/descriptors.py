#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Project: Ubermag
Path:    include/Uberwidgets/metadata/descriptors.py

Description:
    Short description of what this (descriptors.py) does.
    
Author:      Cameron Aidan McEleney < c.mceleney.1@research.gla.ac.uk >
Created:     25 Apr 2025
IDE:         PyCharm
Version:     0.1.0
"""

# Standard library imports
from typing import Any
# Third-party imports

# Local application imports

__all__ = [
    "_DmiDescriptor",
    "_NoDmiRebind",
    "_dmi_desc"
]


class _DmiDescriptor:
    """
    Descriptor for controlling the DMI flag on EnableEnergyTerm.

    When accessed on the class, returns the default boolean.  When accessed
    on an instance, returns either False or the per-instance dict.  Setting
    to True populates the dict; setting to False resets each key to False.

    Attributes
    ----------
    default : bool
        Stored class-level default.
    _name : str
        Name of the attribute this descriptor was assigned to.
    _private : str
        Instance's private attribute name for `dataclasses.field()`
    _dmi_flags : dict[str, bool]
        Default values for possible DMI configuration cases.

    Raises
    ------
    AttributeError
        If someone attempts to overwrite the class-level definition `EnableEnergyTerm.dmi`. This would cause the
        descriptor to be set to a different type, which is not allowed.

    Examples
    --------
    >>> from enable_energy_terms import EnableEnergyTerms
    >>> EnableEnergyTerm.dmi
    False
    >>> inst = EnableEnergyTerm(dmi=True)
    >>> inst.dmi
    {'constant': True, 'dictionary': False, 'subregions': False}
    """
    def __init__(self):
        self.default = False  # Class-level definition for "Is DMI enabled by default"
        self._name = None
        self._dmi_flags = {
            "constant":   True,
            "dictionary": False,
            "subregions": False,
        }

    def __set_name__(self, owner, name):
        # capture the attribute name (“dmi”)
        self._name = name
        self._private = f"_{name}"

    def __get__(self, instance, owner=None):
        if instance is None:
            # class‐level access -> return the declared default
            return self.default
        # instance‐level -> return whatever _<name> was set to, or default
        return getattr(instance, self._private, self.default)

    def __set__(self, instance, flag: bool):
        # Whenever someone does inst.dmi = True/False e.g. `has_energy=EnableEnergyTerm();has_energy.dmi = True`
        if instance is None:
            raise AssertionError(f"You cannot set the class-wide behaviour!")

        if flag:
            instance.__dict__[self._private] = self._dmi_flags
        else:
            if self._private in instance.__dict__:
                instance.__dict__[self._private] = {key: False for key, _ in self._dmi_flags.items()}
            # else: never enabled—and that’s fine, no change


class _NoDmiRebind(type):
    """
    Prevents DMI custom decorator being overwritten at the base-class level by EnableEnergyTerm.dmi = False.

    Attributes
    ----------

    Raises
    ------
    AttributeError
        If someone attempts to overwrite the class-level definition `EnableEnergyTerm.dmi`. This would cause the
        descriptor to be set to a different type, which is not allowed.

    See Also
    --------
    _DMIDescriptor
    """
    def __setattr__(cls, name: str, value: Any):
        if name == "dmi":
            raise AttributeError("You may not override the `dmi` descriptor on the class")
        super().__setattr__(name, value)


# one shared descriptor instance with its default baked in
_dmi_desc = _DmiDescriptor()
