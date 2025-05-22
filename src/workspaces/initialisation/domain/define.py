#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Project: UbermagGUI
Path:    src/workspaces/initialisation/domain/define.py

DefineDomainRegion:
    UI to set up the main Region (pmin, pmax, cellsize, units).
    Inherits all layout + callback wiring from _PanelBase.
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
    "DefineDomainRegion"
]

logger = logging.getLogger(__name__)


class DefineDomainRegion(_PanelBase):
    """
    A panel that lets you create a new primary region (domain).

    Attributes
    ----------
    pmin : "ThreeCoordinateInputs"
        Bottom corner of the region.

    pmax : "ThreeCoordinateInputs"
        Upper corner of the region.

    cell : "ThreeCoordinateInputs"
        Dimensions for the unit cell.

    units_dd : widgets.DropDown
        User can select their unit-base for all entered values via a
        Dropdown of S.I. prefixes.

    btn_define : widgets.Button
        Button to trigger the creation of the `df.Region`.

    btn_reset : widgets.Button
        Button to trigger the clearing of the ``main_region`` stored in the interface's
        ``_CoreProperties`` instance.


    """
    # placeholders for widgets whose value we read later
    pmin: ThreeCoordinateInputs
    pmax: ThreeCoordinateInputs
    cell: ThreeCoordinateInputs

    units_dd: widgets.Dropdown
    btn_define: widgets.Button
    btn_reset: widgets.Button

    def __init__(self):
        super().__init__()

        # placeholders for widgets whose value we read later
        self.pmin = ThreeCoordinateInputs(None, None, None)
        self.pmax = ThreeCoordinateInputs(None, None, None)
        self.cell = ThreeCoordinateInputs(None, None, None)

    def _assemble_panel(self, children: typing.List[widgets.Widget]) -> None:

        children.append(widgets.HTML("<b>Define domain.</b>"))

        children.append(widgets.HTML(
            value=(
                "Create a cuboid domain that encapsulates the entire system. "
                "First, set the units all dimensions will be expressed in."
            ), #layout=widgets.Layout(overflow_y="visible")
        ))

        children.append(self._make_units_dropdown())

        children.extend(self._make_position_and_cell_widgets())

        children.append(self._make_buttons())

    def _make_units_dropdown(self) -> widgets.HBox:
        html_units = widgets.HTML(value='Units')

        self.units_dd = widgets.Dropdown(
            options=UNIT_FACTORS.keys(),
            value=self._sys_props.units[0],
            layout=widgets.Layout(width="40%",)
        )

        box = widgets.HBox(
            children=[html_units, self.units_dd],
            layout=widgets.Layout(
                width='auto',
                height='auto',
                align_items='center',
                align_content='center',
                justify_content='flex-end',
            ),
        )

        return box

    def _make_position_and_cell_widgets(self) -> list[widgets.Widget]:

        out: list[widgets.Widget] = []

        # Might copy & reference Ubermag's df.Region.pmin docstring in the future
        out.append(widgets.HTML(
            value="Define the two diagonally-opposite corners of the domain:",
            layout=widgets.Layout(overflow_y="visible", align_content="stretch", justify_content="flex-start",)
        ))

        self.pmin = ThreeCoordinateInputs.from_defaults(r"\(\mathbf{p}_1\)", (0, 0, 0))
        out.append(self.pmin.hbox)

        self.pmax = ThreeCoordinateInputs.from_defaults(r"\(\mathbf{p}_2\)", (1, 1, 1))
        out.append(self.pmax.hbox)

        out.append(widgets.HTML(
            value="Then specify the mesh cell‐size:",
            layout=widgets.Layout(overflow_y="visible",
                                  align_content="stretch",
                                  justify_content="flex-start",)
        ))
        self.cell = ThreeCoordinateInputs.from_defaults(r"\(\Delta d\)", self._sys_props.cell)
        out.append(self.cell.hbox)

        return out

    def _make_buttons(self):
        """Buttons to define and initialise, and reset the domain."""

        self.btn_define = widgets.Button(
            description="Initialise domain",
            style={"button_style": "info"},
        )

        self.btn_reset = widgets.Button(
            description="Reset domain",
            style={"button_style": "info"},
            disabled=True,
        )

        # always wire the click -> our handler; callback stored in self._ctrl_cb
        if self._ctrl_cb:
            self.btn_define.on_click(self._on_define)
            self.btn_reset.on_click(self._on_reset)

        box = widgets.HBox(
            [self.btn_define, self.btn_reset],
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
        logger.debug("DefineDomainRegion._on_define called; pmin=%r, pmax=%r, units=%r",
                     self.pmin.values, self.pmax.values, self.units_dd.value)

        # unit → SI factor
        self._sys_props._units = (self.units_dd.value, self.units_dd.value, self.units_dd.value)
        user_si_prefix = UNIT_FACTORS[self._sys_props._units[0]]

        # convert to SI
        p1 = tuple(v * user_si_prefix for v in self.pmin.values)
        p2 = tuple(v * user_si_prefix for v in self.pmax.values)
        cell = tuple(v * user_si_prefix for v in self.cell.values)
        self._sys_props._cell = cell

        try:
            # build the Region (SI coords, tagged with user units)
            region = df.Region(
                p1=p1, p2=p2,
                dims=self._sys_props.dims,
                units=self._sys_props.units
            )
        except Exception:
            # TODO. Cease catch all with better debugging
            logger.exception("Domain initialisation failed")
            self.btn_define.button_style = "danger"
            return

        # 1) update interface controller via callback
        if self._ctrl_cb:
            self._ctrl_cb(region)

        # 3) UI feedback
        self.btn_define.disabled = True
        self.btn_define.button_style = 'success'
        self.btn_reset.disabled = False
        self.btn_reset.button_style = ''

        logger.success("DefineDomainRegion._on_define: call complete.")

    def _on_reset(self, _):
        """User clicked 'Reset domain': clear and redraw empty."""
        # clear via controller callback
        if self._ctrl_cb:
            self._ctrl_cb(None)

        # UI feedback
        self.btn_define.disabled = False
        self.btn_define.button_style = ''
        self.btn_reset.disabled = True
        self.btn_reset.button_style = 'danger'

    def refresh(self, *args: typing.Any) -> None:
        """
        No dynamic ``ipywidgets.DropDown`` here, so there's nothing to refresh.
        """
        pass
