#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Project: UbermagGUI
Path:    src/builder.py

UbermagInterface:
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
from contextlib import ContextDecorator
import dataclasses


# Third-party imports
import micromagneticmodel as mm
import discretisedfield as df

# Local application imports
import src.config as cfg
from src.workspaces.workspace_controller import WorkspaceController
from src.viewports.viewports_controller import ViewportsController
from src.outliners.outliner_controller import OutlinerController
from src.helper_functions import units_to_meter_factors
from src.config.dataclass_containers import _CoreProperties

__all__ = ["UbermagInterface"]


class UbermagInterface:
    def __init__(
            self,
            system_name: str = "mySystem",
            cellsize: cfg.UbermagCellsizeType = (1, 1, 1),
            dims: cfg.UbermagDimsType = ("x", "y", "z"),
            units: cfg.UbermagUnitsType = ("nm", "nm", "nm"),
            show_borders: bool = True,
    ):
        # 1) configure logging
        cfg.setup_logging(console_level="WARNING", file_level="INFO")
        logging.getLogger("Comm").setLevel(logging.WARNING)
        self.logger = logging.getLogger(__name__)
        self.logger.info("Starting UbermagInterface")

        # 2) core micromagnetic system
        self.interface_properties = _CoreProperties(initial_system=mm.System(name=system_name))

        # 4) viewport (3D plotting area)
        self.viewports = ViewportsController(properties_controller=self.interface_properties)

        # 5.1) workspace controller (Geometry + System Init + ...)
        self.workspaces = WorkspaceController(
            properties_controller=self.interface_properties,
            plot_callback=self.viewports.plot_regions,
        )
        # 5.2) outliner controller (show regions + ...)
        self.outliner = OutlinerController(
            properties_controller=self.interface_properties,
            workspace_controller=self.workspaces
        )

        # 6) status bar
        self.status_bar = self._assemble_status_bar()  # TODO. Turn StatusBar into its own dir. with own controller.

        # 7) header
        self.top_menu = self._assemble_top_menu()  # TODO. Turn TopMenu into its own dir. with own controller.

        # This is the full user interface
        self.ui = self._build_interface()

        # Optional borders
        if show_borders:
            for pane in (self.ui[0, 0], self.ui[1, 0], self.ui[1, 1], self.ui[2, 0]):
                pane.layout.border = '1px solid gray'
                for child in getattr(pane, 'children', []):
                    child.layout.border = '1px solid blue'

        display(self.ui)

    def _build_interface(self):
        # Main GridspecLayout: 3 rows x 2 cols
        grid = widgets.GridspecLayout(
            n_rows=3, n_columns=2,
            layout=widgets.Layout(
                min_width='600px',
                min_height='600px', # max_height='800px',
                gap='4px',
            )
        )

        grid._grid_template_rows = '1fr 8fr 1fr'
        grid._grid_template_columns = '3fr 2fr'

        # Allocate each controller in the grid; hooking their wiring.
        grid[0, :] = self.top_menu if self.top_menu else widgets.HTML('')
        grid[1, 0] = self.viewports.build()
        grid[1, 1] = self._assemble_workspace_and_outliner_column()
        grid[2, :] = self.status_bar if self.status_bar else widgets.HTML('')

        return grid

    def _assemble_top_menu(self) -> widgets.HBox:

        container = widgets.HBox(
            # TODO. Perhaps child should be `self.controller.build_top_menu()`?
            children=[self.viewports.build_selector_for_top_menu(),
                      self.workspaces.build_selector_for_top_menu()],
            layout=widgets.Layout(justify_content='flex-start', gap='4px')
        )

        return container

    @staticmethod
    def _assemble_status_bar() -> widgets.HBox:
        btn_instant = widgets.Button(
            description='Instantiate', layout=widgets.Layout(width='auto')
        )
        container = widgets.HBox([btn_instant], layout=widgets.Layout(justify_content='flex-end'))

        return container

    def _assemble_workspace_and_outliner_column(self) -> widgets.GridspecLayout:
        """
        Combine Workspace-controller with Outliner-controller inputs to create a VBox output that the
        interface will display.
        """
        grid = widgets.GridspecLayout(
            n_rows=2, n_columns=1,
            layout=widgets.Layout(
                width='100%', height='100%',
                gap='4px',
                min_height='0',
                overflow='auto'
            )
        )
        grid._grid_template_rows = '3fr 7fr'

        grid[0, 0] = self.outliner.build()
        grid[1, 0] = self.workspaces.build()

        return grid


def main():
    UbermagInterface()


if __name__ == "__main__":
    main()
