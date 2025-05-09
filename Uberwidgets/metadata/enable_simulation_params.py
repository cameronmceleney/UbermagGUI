#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Project: Ubermag
Path:    include/Uberwidgets/metadata/enable_simulation_params.py

Description:
    Short description of what this (enable_simulation_params.py) does.
    
Author:      Cameron Aidan McEleney < c.mceleney.1@research.gla.ac.uk >
Created:     25 Apr 2025
IDE:         PyCharm
Version:     0.1.0
"""

# Standard library imports
from dataclasses import dataclass, field, Field
from typing import Any, ClassVar
# Third-party imports

# Local application imports
from field_info import FieldInfo

__all__ = ["EnableSimulationParameters"]


@dataclass
class EnableSimulationParameters:
    """
    Container for simulation parameters.

    Attributes
    ----------
    driving_frequency : float
        Frequency of the driving field.

    saturation_magnetisation : float
        Saturation magnetisation of the material.

    simulation_stepsize : float
        Stepsize for the simulation.

    num_subdivisions : int
        Number of subdivisions for the simulation. Used to discretise particular subregions.

    Examples
    --------
    >>> params = EnableSimulationParameters(
    ...     driving_frequency=10.0,
    ...     saturation_magnetisation=8e5,
    ...     simulation_stepsize=0.01,
    ...     num_subdivisions=1
    ... )
    >>> params.driving_frequency
    10.0
    """

    # This line is simply to make my IDE happy!
    __dataclass_fields__: ClassVar[dict[str, Field[Any]]]

    driving_frequency: int | float = field(
        default=10.00,
        metadata=FieldInfo(
            label='Driving frequency',
            symbol=r'$f_\text{d}$',
            units={'frequency': 'GHz'},
            group='driving field'
        )
    )
    saturation_magnetisation: float | int = field(
        default=8e5,
        metadata=FieldInfo(
            label='Saturation magnetisation',
            symbol=r'$M_{s}$',
            units={'magnetic field': r'$A m^{-1}$'},
        )
    )

    simulation_stepsize: float | int = field(
        default=0.01,
        metadata=FieldInfo(
            label='Simulation stepsize',
            symbol=r'$h$',
            units={'time': 'ns'},
        )
    )

    num_subdivisions: int = field(
        default=1,
        metadata=FieldInfo(
            label='Number of subdivisions',
            symbol=r'$N_\text{sub}$',
            units={'subdivisions': ''},
        )
    )

    @classmethod
    def _read_metadata(cls, attribute_name: str, metadata_property: str = ''):

        if attribute_name not in cls.__dict__:
            raise AttributeError(f"{attribute_name} not found in {cls.__name__}")

        if metadata_property == '':
            return dict(cls.__dataclass_fields__['exchange'].metadata).keys()
        elif metadata_property not in cls.__dataclass_fields__[attribute_name].metadata.keys():
            raise AttributeError(f"{metadata_property} not found in {cls.__name__}")

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
