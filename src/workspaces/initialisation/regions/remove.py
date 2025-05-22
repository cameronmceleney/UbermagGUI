#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Project: UbermagGUI
Path:    src/workspaces/initialisation/regions/remove.py

Description:
    RemoveRegion: region dropdown + Delete button.
    This panel allows the user to select an existing subregion and remove it
    from the model, updating the Outliner and Viewport accordingly.
Author:      Cameron Aidan McEleney < c.mceleney.1@research.gla.ac.uk >
Created:     29 Apr 2025
Version:     0.1.1
"""
# Standard library imports
import logging
import ipywidgets as widgets
from typing import Any

# Third-party imports

# Local application imports
from src.workspaces.initialisation.panels import _PanelBase

__all__ = ["RemoveRegion"]

logger = logging.getLogger(__name__)


class RemoveRegion(_PanelBase):
    """
    RemoveRegion panel:

    Attributes
    ----------
    dd_regions : widgets.Dropdown
        Dropdown listing all current subregions.

    btn_delete : widgets.Button
        Button to remove the selected region.
    """
    def __init__(self):
        super().__init__()

    def _assemble_panel(self, children: list[widgets.Widget]) -> None:

        children.append(
            widgets.HTML("<b>Remove region.</b>")
        )

        children.append(
            widgets.HTML(value="Remove a saved region from the system. This also removes it "
                               "from any instances in which it is a subregion.",
                         layout=widgets.Layout(width="auto")
                         )
        )

        children.append(self._make_dropdown_row())

        children.append(self._make_remove_button())

    def _make_dropdown_row(self) -> widgets.HBox:

        label = widgets.HTML(value="Target region", layout=widgets.Layout(width="auto"))

        # Build dropdown from current regions
        self.dd_regions = widgets.Dropdown(
            options=list(self._sys_props.regions.keys()),
            layout=widgets.Layout(width="40%")
        )
        hbox = widgets.HBox(
            [label, self.dd_regions],
            layout=widgets.Layout(
                align_items="center",
                justify_content="flex-end",
                gap="4px"
            )
        )

        return hbox

    def _make_remove_button(self) -> widgets.HBox:
        self.btn_delete = widgets.Button(
            description="Delete region",
            style={"button_style": ""},
            layout=widgets.Layout(width="auto")
        )
        # wire up the click only if callback is already set
        if self._ctrl_cb:
            self.btn_delete.on_click(self._on_delete)

        hbox = widgets.HBox(
            [self.btn_delete],
            layout=widgets.Layout(justify_content="center", width="100%")
        )

        return hbox

    def _on_delete(self, _: Any) -> None:
        """When the user clicks delete—invoke callback & refresh dropdown."""
        key = self.dd_regions.value
        if not key:
            self.btn_delete.button_style = "danger"
            logger.error("RemoveRegion._on_delete: no region selected to delete.")
            return

        # Notify controller
        if self._ctrl_cb:
            self._ctrl_cb(key)

        self.dd_regions.value = None
        self.btn_delete.button_style = ""

        logger.success("RemoveRegion: deleted %r", key)

    def refresh(self, *_) -> None:
        """
        Update dropdown options to reflect current subregions.
        """
        if self._sys_props is None or self.dd_regions is None:
            return

        # remember old selection
        old = self.dd_regions.value

        # repopulate—don’t auto‐pick first if old is gone
        self._refresh_dropdown(
            self.dd_regions,
            self._sys_props.regions.keys(),
            labeler=str,
            default_first=False
        )

        # if the old is still valid leave it, otherwise clear
        if old in self._sys_props.regions:
            self.dd_regions.value = old
        else:
            self.dd_regions.value = None