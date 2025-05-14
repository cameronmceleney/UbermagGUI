#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Project: UbermagGUI
Path:    src/viewports/viewports_controller.py

Description:
    Short description of what this (viewports_controller.py) does.
    
Author:      Cameron Aidan McEleney < c.mceleney.1@research.gla.ac.uk >
Created:     13 May 2025
IDE:         PyCharm
Version:     0.1.0
"""

# Standard library imports
import ipywidgets as widgets
from IPython.display import display

# Third-party imports

# Local application imports
from src.viewports.threeD.plotly_3dmesh import Mesh3DPlot

__all__ = [
    "Viewport3DFeature",
    "ViewportsController"
]


class Viewport3DFeature:
    """A single “3D mesh” view for the ViewportsController."""
    def __init__(self):
        self.mesh_plot = Mesh3DPlot()
        self.btn_reset = widgets.Button(description="Reset Camera")
        self.btn_reset.on_click(lambda _: self.mesh_plot.reset_camera())
        self.viewport_toolbar = self._build_toolbar()

    def build(self) -> widgets.GridspecLayout:
        grid = widgets.GridspecLayout(
            n_rows=2, n_columns=1,
            layout=widgets.Layout(width='100%', height='100%', gap='4px')
        )
        grid._grid_template_rows = '9fr 1fr'

        fig_box = widgets.Box(
            [self.mesh_plot.fig],
            layout=widgets.Layout(
                # display='flex',
                # flex="0 1 auto",
                # #width='auto', height='auto',
                # align_items='stretch'
                # overflow="hidden"  # Prevents weird rendering of plot labels if fig-space is too small
            )
        )
        grid[0, 0] = fig_box
        grid[1, 0] = self.viewport_toolbar
        return grid

    def _build_toolbar(self) -> widgets.HBox:
        """Intentionally keeping toolbar creation separate for inclusion of future implementations."""
        toolbar_container = widgets.HBox(
            children=[self.btn_reset],
            layout=widgets.Layout(justify_content='flex-start')
        )

        return toolbar_container

    def plot(self, main_region, subregions, show_domain=True):
        self.mesh_plot.plot(main_region, subregions, show_domain)


class ViewportsController:
    """
    Allows switching between multiple viewport features.
    Currently, only “3D” is implemented.
    """
    def __init__(self):
        self.features = {
            '3D view': Viewport3DFeature(),
            # future: '2D': Viewport2DFeature(),
        }

        # Viewport's ToggleButtons will be positioned: left-side of 'Top Menu'
        self.selector = widgets.ToggleButtons(
            options=list(self.features),
            description='View:',
            layout=widgets.Layout(width='auto'),
            style={'button_width': 'auto'}
        )
        self.content = widgets.Output(
            layout=widgets.Layout(width='100%', height='100%', overflow='hidden')
        )

        self.selector.observe(self._on_select, names='value')

    def _on_select(self, change):
        if change.get('name') == 'value':
            self.content.clear_output()
            with self.content:
                display(self.features[change['new']].build())

    def build(self):
        # initialise the content to the first feature (selector is held elsewhere)
        first = list(self.features)[0]
        self.selector.value = first

        # return only the content area – selector lives in the top‐menu
        return self.content

    def build_selector_for_top_menu(self):
        """Intentionally separated out the selector bar for the TopMenu UI area"""
        container = widgets.HBox(
            children=[self.selector],
            layout=widgets.Layout(justify_content='flex-start')
        )
        return container

    def plot_regions(self, main_region, subregions, show_domain=True):
        """Route data → currently‐selected viewport feature."""
        feat = self.features[self.selector.value]
        feat.plot(main_region, subregions, show_domain)
