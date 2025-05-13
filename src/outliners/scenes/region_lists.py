#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Project: UbermagGUI
Path:    src/outliners/scenes/region_lists.py

Description:
    Short description of what this (region_listings.py) does.
    
Author:      Cameron Aidan McEleney < c.mceleney.1@research.gla.ac.uk >
Created:     12 May 2025
IDE:         PyCharm
Version:     0.1.0
"""

# Standard library imports
import ipywidgets as widgets
from ipywidgets import Layout

# Third-party imports

# Local application imports

__all__ = ["RegionListReadOnly"]


class RegionListReadOnly:
    """
    Maintains an HTML widget that displays the current main region,
    its named subregions, the mesh cell count, and initial magnetisation.
    """
    def __init__(self):
        # HTML widget that will show the region tree and properties
        self.widget = widgets.HTML(
            '<i>No domain set.</i>',
            layout=Layout(overflow='auto')
        )

    def update(self, main_region, subregions, mesh=None, init_mag=None):
        """
        Update the HTML content based on the provided state.
        """
        if main_region is None:
            self.widget.value = '<i>No domain set.</i>'
            return

        html = ['<ul><li>main_region']
        for name in subregions:
            html.append(f"<ul><li>{name}</li></ul>")
        html.append('</li></ul>')

        if mesh is not None:
            n = getattr(mesh, 'n', None)
            if n is not None:
                html.append(f"<p><b>Mesh cells:</b> {n}</p>")

        if init_mag is not None:
            val  = getattr(init_mag, 'value', None)
            norm = getattr(init_mag, 'norm',  None)
            html.append(
                "<p><b>Init mag:</b> "
                f"value={val}" + (f", norm={norm}" if norm is not None else "")
                + "</p>"
            )

        self.widget.value = ''.join(html)
