#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Project: Ubermag
Path:    include/Uberwidgets/metadata/enable_energy_terms.py

Description:
    Short description of what this (enable_energy_terms.py) does.
    
Author:      Cameron Aidan McEleney < c.mceleney.1@research.gla.ac.uk >
Created:     25 Apr 2025
IDE:         PyCharm
Version:     0.1.0
"""

# Standard library imports
from dataclasses import dataclass, field, Field, InitVar
from typing import Any, ClassVar
# Third-party imports

# Local application imports
from descriptors import _DmiDescriptor, _NoDmiRebind
from field_info import FieldInfo

__all__ = [
    "EnableEnergyTerms"
]

# one shared descriptor instance with its default baked in
_dmi_desc = _DmiDescriptor()

anisotropy_metadata = FieldInfo(
    label='Anisotropy',
    symbol=r'$\mathbf{H}_A$',
    options=[r'$\mathbf{H}_A$', r'$\mathbf{H}_{ua}$'],
    units={'Mag field': r'$A/m$'},
    group='energy',
)

demag_metadata = FieldInfo(
    label='Demagnetisation',
    symbol=r'$\mathbf{H}_\text{demag}$',
    options=[r'$\mathbf{H}_\text{demag}$'],
    units={'Magnetic field': r'$A m^{-1}$'},
    group='energy',
)

static_zeeman_metadata = FieldInfo(
    label='Static Zeeman',
    symbol=r'$\mathbf{H}_\text{0}$',
    options=[r'$\mathbf{H}_\text{0}$'],
    units={'Magnetic field': r'$A m^{-1}$',
           'Magnetic field strength': r'$A m^{-1}$'
           },
    group='energy',
)

driving_zeeman_metadata = FieldInfo(
    label='Driving Zeeman',
    symbol=r'$\mathbf{h}_\text{drive}$',
    options=[r'$\mathbf{h}_\text{drive} (x,t)$',
             r'$\mathbf{h}_\text{drive} (x)$'],
    units={'Magnetic field': r'$A m^{-1}$',
           'Driving field strength': r'$A m^{-1}$',
           'Time parameters': r'$s$',
           },
    group='energy',
)

exchange_metadata = FieldInfo(
    label='(Heisenberg) Exchange interaction',
    symbol=r'$\mathbf{H}_\text{eff}$',
    options=[r'$\mathbf{H}_\text{eff}$'],
    units={'Magnetic field': r'$A m^{-1}$',
           'Exchange stiffness': r'$J m^{-1}$'
           },
    group='energy',
)

dmi_metadata = FieldInfo(
    label='Dzyaloshinskii-Moriya interaction',
    symbol=r'$\mathbf{H}_\text{DMI}$',
    options=[r'$\mathbf{H}_\text{DMI}$'],
    units={'Magnetic field': r'$A m^{-1}$',
           'DMI constant': r'$J m^{-2}$',
           },
    group='energy',
)


@dataclass
class EnableEnergyTerms(metaclass=_NoDmiRebind):
    """
    Configuration of which energy terms to include in a micromagnetic simulation.

    Each boolean flag toggles a particular effective field contribution:
        - anisotropy
        - demagnetisation
        - static (equilibration) Zeeman
        - driving (time-dependent) Zeeman
        - Heisenberg exchange
        - Dzyaloshinskii–Moriya interaction (via .dmi descriptor)

    Attributes
    ----------
    anisotropy : bool, default: False
        If True, include the uniaxial/cubic anisotropy field.
    demag : bool, default=False
        If True, include the magnetostatic (demagnetisation) field.
    static_zeeman : bool, default=False
        If True, apply a constant Zeeman field for equilibration.
    driving_zeeman : bool, default=False
        If True, apply a time-varying Zeeman drive field.
    exchange : bool, default=False
        If True, include the Heisenberg exchange effective field.
    dmi : bool, default=False
        If True, enable the Dzyaloshinskii–Moriya interaction and populate
        the `.dmi` dict of sub-options (`constant`, `dictionary`, `subregions`).

    Examples
    --------
    >>> e = EnableEnergyTerms(dmi=True)
    >>> e.dmi
    {'constant': True, 'dictionary': False, 'subregions': False}
    >>> EnableEnergyTerms.dmi
    False
    """
    # This line is simply to make my IDE happy!
    __dataclass_fields__: ClassVar[dict[str, Field[Any]]]

    anisotropy: bool = field(default=False, metadata=anisotropy_metadata)

    demag: bool = field(default=True, metadata=demag_metadata)

    static_zeeman: bool = field(default=True, metadata=static_zeeman_metadata)

    driving_zeeman: bool = field(default=True, metadata=driving_zeeman_metadata)

    exchange: bool = field(default=True, metadata=exchange_metadata)

    # Public attribute uses custom descriptor to handle class vs. instance access
    # (instead of using @property decorators)
    dmi: InitVar[bool] = _dmi_desc.default

    # Private attribute that stores the DMI dataclasses.Field object available to EnableEnergyTerm class-instances
    _dmi: bool | dict[str, bool] = field(init=False, repr=False, metadata=dmi_metadata)

    # *Override* the normal dataclass field named "dmi" with our descriptor
    dmi = _dmi_desc

    def __post_init__(self, dmi: bool):
        # dataclasses will call __post_init__(self, dmi_flag)
        self.dmi = dmi

    @classmethod
    def _read_metadata(cls, attribute_name: str, metadata_property: str = ''):

        if attribute_name == '_dmi':
            attribute_name = 'dmi'

        if attribute_name not in cls.__dict__:
            raise AttributeError(f"Attribute_Name | {attribute_name} not found in {cls.__name__}")

        if attribute_name == 'dmi':
            attribute_name = '_dmi'

        if metadata_property not in cls.__dataclass_fields__[attribute_name].metadata.keys():
            raise AttributeError(f"Metadata_Property | {metadata_property} not found in {cls.__name__}")

        return cls.__dataclass_fields__.get(attribute_name).metadata[metadata_property]

    @classmethod
    def label(cls, attribute_name: str):
        return cls._read_metadata(attribute_name, 'label')

    @classmethod
    def name(cls, attribute_name: str):
        return cls.label(attribute_name)

    @classmethod
    def symbol(cls, attribute_name: str):
        return cls._read_metadata(attribute_name, 'symbol')

    @classmethod
    def options(cls, attribute_name: str):
        return cls._read_metadata(attribute_name, 'options')

    @classmethod
    def units(cls, attribute_name: str):
        return cls._read_metadata(attribute_name, 'units')
