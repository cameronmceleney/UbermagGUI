#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Project: Ubermag
Path:    include/Uberwidgets/region_designer_interface/feature_modelling/remove_region.py

Description:
    RemoveRegion: region dropdown + Delete button.
    This panel allows the user to select an existing subregion and remove it
    from the model, updating the Outliner and Viewport accordingly.
Author:      Cameron Aidan McEleney < c.mceleney.1@research.gla.ac.uk >
Created:     29 Apr 2025
Version:     0.1.1
"""

import ipywidgets as widgets
from ipywidgets import Layout

__all__ = ["RemoveRegion"]


class RemoveRegion:
    def __init__(self):

        # callbacks from ControlsPanel
        self._state_cb = None  # ControlsPanel.remove_subregion
        self._plot_cb = None   # ViewportArea.plot_regions
        self._controls = None

        # widgets
        self.dd_regions_in_domain = None
        self.btn_delete = None

    def set_state_callback(self, cb):
        """Register ControlsPanel.remove_subregion."""
        self._state_cb = cb

    def set_plot_callback(self, func):
        """Register ViewportArea.plot_regions and bind delete click."""
        self._plot_cb = func

    def build(self, controller) -> widgets.VBox:
        """
        Build and return the UI for removing a subregion.
        Captures controller to access current subregions.
        """
        self._controls = controller

        # Dynamically collect children
        remove_panel = widgets.VBox(
            layout=Layout(
                width='auto',
                height='auto',
                overflow="auto",
                padding="4px"
            ),
        )
        panel_children = []

        # Introductory text to the panel
        html_explainer = widgets.HTML(
            value="Remove an existing region from the domain.",
            layout=widgets.Layout(
                width='auto',
            )
        )
        panel_children.append(html_explainer)

        # Create DropDown by populating with subregions from ControlsPanel
        html_regions_in_domain = widgets.HTML(
            value="Target region",
        )

        self.dd_regions_in_domain = widgets.Dropdown(
            options=list(self._controls.subregions.keys()),
            layout=Layout(width="40%")
        )

        hbox_regions_in_domain = widgets.HBox(
            children=[html_regions_in_domain, self.dd_regions_in_domain],
            layout=Layout(
                width='auto',
                height='auto',
                align_items='center',
                align_content='center',
                justify_content='flex-end',
            )
        )
        panel_children.append(hbox_regions_in_domain)

        # Button to allow user interaction
        self.btn_delete = widgets.Button(
            description="Delete Region",
            style={'button_width': 'auto',
                   'button_style': ''},
        )
        self.btn_delete.on_click(self._on_delete)

        btn_box = widgets.HBox(
            [self.btn_delete],
            layout=Layout(justify_content='center', width='auto')
        )
        panel_children.append(btn_box)

        remove_panel.children = tuple(panel_children)
        return remove_panel

    def _refresh(self):
        remaining = list(self._controls.subregions.keys())
        self.dd_regions_in_domain.options = remaining
        # Do not reset .value to another region; can lead to accidental deletion if click is spammed!
        self.dd_regions_in_domain.value = None

        # Reset button color; avoids confusion
        self.btn_delete.button_style = ''

        # Redraw via Viewport callback
        if self._plot_cb:
            self._plot_cb(
                self._controls.main_region,
                self._controls.subregions,
                self._controls.toggle_show.value,
            )

    def refresh(self):
        self._refresh()

    def _on_delete(self, _):
        """Handle deletion: notify ControlsPanel, then redraw."""
        region_name = self.dd_regions_in_domain.value
        if not region_name or region_name is None:
            self.btn_delete.button_style = 'danger'
            return

        # 1) remove via ControlsPanel
        if self._state_cb:
            self._state_cb(region_name)

        # 2) Refresh dropdown
        self._refresh()
