#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Project: UbermagGUI
Path:    src/workspaces/equations/energy/zeeman.py

Description:
    Short description of what this (zeeman.py) does.
    
Author:      Cameron Aidan McEleney < c.mceleney.1@research.gla.ac.uk >
Created:     22 May 2025
IDE:         PyCharm
Version:     0.1.0
"""
# Standard library imports
import logging
import ipywidgets as widgets
import typing

# Third-party imports
import discretisedfield as df

# Local application imports
from src.config.type_aliases import UNIT_FACTORS
from src.workspaces.initialisation.panels import _PanelBase,ThreeCoordinateInputs

__all__ = [
    "StaticZeeman"
]

logger = logging.getLogger(__name__)


class StaticZeeman(_PanelBase):
    """
    Create a test panel for the Energy feature.

    Attributes
    ----------
    btn_define : widgets.Button
        Button to signal that callbacks should take place to define a 'static' ``micromagneticmodel.Zeeman`` term.
    """
    # placeholders for widgets whose value we read later
    btn_define: widgets.Button

    def __init__(self):
        super().__init__()

    def _assemble_panel(self, children: typing.List[widgets.Widget]) -> None:

        children.append(widgets.HTML("<b>Define a static Zeeman EnergyTerm.</b>"))

        children.append(self._make_buttons())

    def _make_buttons(self):
        """Buttons to define and initialise, and reset the domain."""

        self.btn_define = widgets.Button(
            description="Test button",
            style={"button_style": "info"},
        )

        # always wire the click -> our handler; callback stored in self._ctrl_cb
        if self._ctrl_cb:
            self.btn_define.on_click(self._on_define)

        box = widgets.HBox(
            [self.btn_define],
            layout=widgets.Layout(
                width='auto',
                height='auto',
                align_items="center",
                align_content="center",
                justify_content='space-around'
            )
        )

        return box

    def _on_define(self, _):
        """User clicked: ‘Initialise Domain’.

        Convert UI inputs to S.I., build ``discretisedfield.Region``, and call controller callback.
        """
        logger.debug("StaticZeeman._on_define called.")

        # Update interface controller via callback
        if self._ctrl_cb:
            self._ctrl_cb

        # 3) UI feedback
        self.btn_define.button_style = 'success'

        logger.success("StaticZeeman: call complete.")

    def refresh(self, *args: typing.Any) -> None:
        """
        No dynamic ``ipywidgets.DropDown`` here, so there's nothing to refresh.
        """
        pass
