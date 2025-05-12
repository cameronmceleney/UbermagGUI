#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Project: UbermagGUI
Path:    src/new_builder.py

Description:
    Orchestrates construction of the RegionDesigner by composing
    header, viewport, controls, and footer modules into a grid layout.
    
Author:      Cameron Aidan McEleney < c.mceleney.1@research.gla.ac.uk >
Created:     12 May 2025
IDE:         PyCharm
Version:     0.1.0
"""

# Standard library imports
import logging
from IPython.display import display
import ipywidgets as widgets

# Third-party imports
import micromagneticmodel as mm

# Local application imports
import src.config as cfg
from src.workspaces.workspace_controller import WorkspaceController
#from src.workspaces.viewport.viewport import ViewportArea
#from src.workspaces.status_bar.status_bar import StatusBar
from src.helper_functions import units_to_meter_factors

__all__ = ["RegionDesigner"]


class RegionDesigner:
    def __init__(
            self,
            system_name: str = "mySystem",
            cellsize: cfg.UbermagCellsizeType = (1, 1, 1),
            dims: cfg.UbermagDimsType = ("x", "y", "z"),
            units: cfg.UbermagUnitsType = ("nm", "nm", "nm"),
            show_borders: bool = True,
    ):
        # 1) configure logging
        cfg.setup_logging(console_level="INFO")
        self.logger = logging.getLogger(__name__)
        self.logger.info("Starting RegionDesigner")

        # 2) core micromagnetic system
        self.system = mm.System(name=system_name)

        # 3) convert user units → SI
        # Units are only Ubermag property that can't be nicely stored in System
        # during user's first interactions
        self.units = units_to_meter_factors(units)

        # 4) viewport (3D plotting area)
        self.viewport_area = None  # ViewportArea()

        # 5) workspace controller (Geometry + System Init + …)
        self.controller = WorkspaceController(
            system=self.system,
            plot_callback=self.viewport_area.plot_regions
        )

        # 6) status bar
        self.status_bar = None  # StatusBar()

        # 7) header (just reuse the controller’s top menu)
        self.header = self.controller.build_top_menu()

        # This is the full user interface
        self.ui = self._build_interface()

        # Optional borders
        if show_borders:
            for pane in (self.ui[0, 0], self.ui[1, 0], self.ui[1, 1], self.ui[2, 0]):
                pane.layout.border = '1px solid gray'
                for child in pane.children:
                    child.layout.border = '1px solid blue'

        display(self.ui)

    def _build_interface(self):
        # Main GridspecLayout: 3 rows x 2 cols
        grid = widgets.GridspecLayout(
            n_rows=3, n_columns=2,
            layout=widgets.Layout(
                min_width='800px',
                min_height='800px',
                gap='4px',
            )
        )

        grid._grid_template_rows = '1fr 8fr 1 fr'
        grid._grid_template_columns = '3fr 2fr'

        # Allocate each controller in the grid; hooking their wiring.
        grid[0, :] = self.header
        grid[1, 0] = self.viewport_area.build()
        grid[1, 1] = self.controller.build()
        grid[2, :] = self.status_bar.build()

        return grid


def main():
    RegionDesigner()


if __name__ == "__main__":
    main()
