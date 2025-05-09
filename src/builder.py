#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Project: UbermagGUI
Path:    ./src/builder.py

Description:
    Orchestrates construction of the RegionDesigner by composing
    header, viewport, controls, and footer modules into a grid layout.
    
Author:      Cameron Aidan McEleney < c.mceleney.1@research.gla.ac.uk >
Created:     29 Apr 2025
IDE:         PyCharm
Version:     0.1.0
"""

# Standard library imports
from IPython.display import display
from ipywidgets import GridspecLayout, Layout
import logging

# Third-party imports
import micromagneticmodel as mm

# Local application imports
from .config import *
from .config.custom_logging import *
from .workspace_viewport import ViewportArea
from .workspace_modelling import ControlsPanel
from .workspace_status_bar import StatusBar
from helper_functions import units_to_meter_factors

__all__ = ["RegionDesigner"]


class RegionDesigner:
    def __init__(
            self,
            system_name: str = "mySystem",
            cellsize: type_aliases.UbermagCellsizeType = (1, 1, 1),
            dims: type_aliases.UbermagDimsType = ("x", "y", "z"),
            units: type_aliases.UbermagUnitsType = ("nm", "nm", "nm"),
            show_borders=False
    ):
        # configure logging for the entire interface
        setup_logging(console_level="INFO")
        # now everything below will inherit that configuration
        self.logger = logging.getLogger(__name__)
        self.logger.info("Starting RegionDesigner")

        # Initialise Ubermag micromagnetic system
        self.system = mm.System(name=system_name)
        # Units are only Ubermag property that can't be nicely stored in System during user's first interactions
        self.units = units_to_meter_factors(units)

        # Instantiate subcomponents
        self.viewport_area = ViewportArea()
        self.controls_panel = ControlsPanel(cellsize=cellsize, dims=dims, units=units)
        self.status_bar = StatusBar()

        # Build header toggle (inside controls_panel)
        self.header = self.controls_panel.build_header()

        self.grid = self._build_interface()

        # Optional borders
        if show_borders:
            for pane in (self.grid[0, 0], self.grid[1, 0], self.grid[1, 1], self.grid[2, 0]):
                pane.layout.border = '1px solid gray'
                for child in pane.children:
                    child.layout.border = '1px solid blue'

        display(self.grid)

        # Initial draw
        self.controls_panel.register_plot_callback(self.viewport_area.plot_regions)
        self.controls_panel.register_system_callbacks(
            #on_mesh_created=lambda mesh: setattr(self.system, "mesh", mesh),
            #on_initial_magnetisation=lambda field: setattr(self.system, "m", field)
        )
        self.controls_panel.refresh()

    def _build_interface(self) -> GridspecLayout:
        # Main GridspecLayout: 3 rows x 2 cols
        grid = GridspecLayout(
            n_rows=3, n_columns=2,
            layout=Layout(
                width='auto', min_width='800px',
                height='auto', min_height='800px',
                gap='4px',
            )
        )
        grid._grid_template_rows = '15% 70% 15%'
        grid._grid_template_columns = '55% 45%'

        # Place header
        grid[0, :] = self.header
        # Place viewport
        grid[1, 0] = self.viewport_area.build()
        # Place controls (outliner + feature_modelling)
        grid[1, 1] = self.controls_panel.build()
        # Place footer
        grid[2, :] = self.status_bar.build()

        return grid

