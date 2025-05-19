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
import logging
import ipywidgets as widgets
from ipywidgets import Layout

# Third-party imports

# Local application imports

__all__ = ["RegionListReadOnly"]

logger = logging.getLogger(__name__)


class RegionListReadOnly:
    """
    Maintains a HTML widget that displays:
      - active mesh name
      - domain region name
      - list of subregion names
    """
    def __init__(self):
        self.widget = widgets.HTML(
            '<i>No domain set.</i>',
            layout=Layout(overflow='auto')
        )

    def build(self):
        return

    def update(self, mesh_name=None, region_name=None, subregions=None):
        """
        Update the HTML content based on the provided state.

        Parameters
        ----------
        mesh_name : str | None
            Name of the active mesh.
        region_name : str | None
            Name of the main region.
        subregions : list[str]
            Names of the subregions.
        """
        # if no region, nothing to show
        if region_name is None:
            self.widget.value = '<i>No domain set.</i>'
            return

        # map 'main' to 'domain' to be consistent with other panels terminology
        display_region = 'domain' if region_name == 'main' else region_name

        # Start building our HTML
        html_lines = []
        mesh_display = mesh_name if mesh_name is not None else 'None'
        html_lines.append(f'<p><b>Mesh:</b> {mesh_display}</p>')
        html_lines.append(f'<p><b>Region:</b> {display_region}</p>')

        if subregions:
            html_lines.append('<ul>')
            for name in subregions:
                html_lines.append(f'<li>{name}</li>')
            html_lines.append('</ul>')

        # Rendering
        self.widget.value = ''.join(html_lines)

        logger.success(
            "RegionListReadOnly.update: displayed mesh=%r, region=%r, subregions=%r",
            mesh_name, display_region, subregions
        )
