#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Project: Ubermag
Path:    include/Uberwidgets/metadata/field_info.py

Description:
    Dataclasses which group values required to define Ubermag df.Field instances in order to improve readability
    when generating python widgets.
    
Author:      Cameron Aidan McEleney < c.mceleney.1@research.gla.ac.uk >
Created:     25 Apr 2025
IDE:         PyCharm
Version:     0.1.0
"""

from dataclasses import dataclass, field
from typing import Any, Iterator, Mapping

__all__ = [
    "FieldInfo"
]


@dataclass(frozen=True)
class FieldInfo(Mapping[str, Any]):
    """
    Container for widget metadata, which exposes a mapping interface to ensure
    compatability with `dataclasses.field.metadata`.

    FieldInfo bundles the display label, symbol, options, units, and grouping
    information I require to generate widgets dynamically.

    Attributes
    ----------
    label : str
        Label to represent this term on `ipywidgets` interactables like Buttons.
    symbol : str, optional
        LaTeX symbol representation.
    options : list of str, optional
        Alternative symbol options. Useful for displaying different representations of a magnetic field;
        particularly if the associated energy term has multiple possible options. For example, in Ubermag one
        could define a uniaxial or cubic anisotropy field, which are represented by different symbols.
    units : dict of str to str, optional
        Mapping of physical units to their LaTeX strings.
    group : str, optional
        Logical grouping name for UI organization. Mainly used for debugging.

    Examples
    --------
    >>> info = FieldInfo(
    ...     label="Anisotropy",
    ...     symbol=r"$\\mathbf{H}_A$",
    ...     options=[r"$\\mathbf{H}_A$", r"$\\mathbf{H}_{ua}$"],
    ...     units={"Magnetic field": r"$A m^{-1}$"},
    ...     group="energy"
    ... )
    >>> info["label"]
    'Anisotropy'
    >>> info.label
    'Anisotropy'
    >>> repr(info)
    {'label': 'Anisotropy', 'symbol': '$\\mathbf{H}_A$', 'options': ['$\\mathbf{H}_A$', '$\\mathbf{H}_{ua}$'], 'units': {'Magnetic field': '$A m^{-1}$'}, 'group': 'energy'}
    """
    label: str
    symbol: str = ''
    options: list[str] = field(default_factory=list)
    units: dict[str, str] = field(default_factory=dict)
    group: str = ''

    def __getitem__(self, key: str) -> Any:
        # Redirect key lookups to the corresponding attribute
        if key in self.__dict__:
            return getattr(self, key)
        raise KeyError(key)

    def __iter__(self) -> Iterator[str]:
        # Iterate over main metadata keys. Must be compatible with __init__
        yield from ("label", "symbol", "options", "units", "group")

    def __len__(self) -> int:
        return len(self.__dict__)

    def __repr__(self) -> str:
        # Dict-like printout
        return repr({k: self[k] for k in self})
