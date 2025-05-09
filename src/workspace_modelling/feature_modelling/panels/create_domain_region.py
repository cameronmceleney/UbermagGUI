#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CreateDomain: enter pmin/pmax, initialize the main region.
"""

import ipywidgets as widgets
import discretisedfield as df
from src.config.type_aliases import UNIT_FACTORS
from src.helper_functions import build_widget_input_values_xyz_tuple


class CreateDomain:
    def __init__(self):
        self._state_cb = None
        self._plot_cb  = None
        self._controls = None

        # placeholders for all widgets
        self.pmin_x = self.pmin_y = self.pmin_z = None
        self.pmax_x = self.pmax_y = self.pmax_z = None
        self.cell_x = self.cell_y = self.cell_z   = None

        self.units_dd  = None
        self.btn_init  = None
        self.btn_reset = None

    def set_state_callback(self, cb):
        """Register ControlsPanel.set_domain (or None)."""
        self._state_cb = cb

    def set_plot_callback(self, cb):
        """Register ViewportArea.plot_regions."""
        self._plot_cb = cb

    def build(self, controls_panel):
        """
        Build and return the UI for initializing the domain,
        complete with pmin/pmax (3 boxes each), cellsize entry,
        units dropdown, and Init/Reset buttons.
        """
        self._controls = controls_panel

        domain_panel = widgets.VBox(
            layout=widgets.Layout(overflow="auto", padding="4px"),
        )
        panel_children = []

        # 1) Explanation
        html_intro_explainer = widgets.HTMLMath(
            value=(
                "Create a cuboid domain that encapsulates the entire system. "
                "First, set the units all dimensions will be expressed in."
            ),
            layout=widgets.Layout(overflow_y="visible")
        )
        panel_children.append(html_intro_explainer)

        # 5) units dropdown
        html_units = widgets.HTML(
            value='Units'
        )
        self.units_dd = widgets.Dropdown(
            options=UNIT_FACTORS.keys(),
            value=controls_panel.units[0],
            layout=widgets.Layout(
                width="40%",
            )
        )

        hbox_units = widgets.HBox(
            children=[html_units, self.units_dd],
            layout=widgets.Layout(
                width='auto',
                height='auto',
                align_items='center',
                align_content='center',
                justify_content='flex-end',
            ),
        )
        panel_children.append(hbox_units)

        self._position_widgets(panel_children)

        self._output_button_widgets(panel_children)

        domain_panel.children = tuple(panel_children)
        return domain_panel


    def refresh(self, bases):
        """No dropdowns here, so no-op."""
        pass

    def _on_initialize(self, _):
        """User clicked ‘Initialise Domain’—convert everything to metres, then build region."""
        try:
            # parse all 9 entries
            pmin_raw = (float(self.pmin_x.value),
                        float(self.pmin_y.value),
                        float(self.pmin_z.value))
            pmax_raw = (float(self.pmax_x.value),
                        float(self.pmax_y.value),
                        float(self.pmax_z.value))
            cell_raw = (float(self.cell_x.value),
                        float(self.cell_y.value),
                        float(self.cell_z.value))

            # unit → SI factor
            unit = self.units_dd.value
            factor = UNIT_FACTORS[unit]

            # convert to SI
            pmin_si = tuple(v * factor for v in pmin_raw)
            pmax_si = tuple(v * factor for v in pmax_raw)
            cell_si = tuple(v * factor for v in cell_raw)

            # propagate globally
            self._controls.units = (unit, unit, unit)
            self._controls.cellsize = cell_si
            # only write back if options‐tab actually has one
            try:
                self._controls.units_dd.value = unit
            except AttributeError:
                pass

            # build the Region (SI coords, tagged with user units)
            region = df.Region(
                p1=pmin_si, p2=pmax_si,
                dims=self._controls.dims,
                units=self._controls.units
            )
        except Exception as e:
            # if anything goes wrong, let’s know
            print("Error in CreateDomain._on_initialize():", e)
            return

        # 1) update ControlsPanel state
        if self._state_cb:
            self._state_cb(region)

        # 2) redraw viewport
        if self._plot_cb:
            self._plot_cb(
                self._controls.main_region,
                self._controls.subregions,
                show_domain=self._controls.toggle_show.value
            )

        # 3) UI feedback
        self.btn_init.disabled = True
        self.btn_init.button_style = 'success'
        self.btn_reset.disabled = False
        self.btn_reset.button_style = ''

    def _on_reset(self, _):
        """User clicked 'Reset domain': clear and redraw empty."""
        # clear via state callback
        if self._state_cb:
            self._state_cb(None)
        # redraw empty viewport
        if self._plot_cb:
            self._plot_cb(None, {}, show_domain=self._controls.toggle_show.value)

        # UI feedback
        self.btn_init.disabled = False
        self.btn_init.button_style = ''
        self.btn_reset.disabled = True
        self.btn_reset.button_style = 'danger'

    def _position_widgets(self, panel_children):

        # Might copy & reference Ubermag's df.Region.pmin docstring in the future
        html_domain_explainer = widgets.HTMLMath(
            value="Define the two diagonally-opposite corners of the domain:",
            layout=widgets.Layout(overflow_y="visible",
                                  align_content="stretch",
                                  justify_content="flex-start",)
        )
        panel_children.append(html_domain_explainer)

        # 2) pmin row
        hbox_pmin = build_widget_input_values_xyz_tuple(r"\(\mathbf{p}_1\)", default=(0, 0, 0))
        panel_children.append(hbox_pmin)
        self.pmin_x = hbox_pmin.children[1]
        self.pmin_y = hbox_pmin.children[2]
        self.pmin_z = hbox_pmin.children[3]

        # 3) pmax row
        hbox_pmax = build_widget_input_values_xyz_tuple(r"\(\mathbf{p}_2\)", default=(1, 1, 1))
        panel_children.append(hbox_pmax)
        self.pmax_x = hbox_pmax.children[1]
        self.pmax_y = hbox_pmax.children[2]
        self.pmax_z = hbox_pmax.children[3]

        html_mesh_explainer = widgets.HTMLMath(
            value="Then specify the mesh cell‐size:",
            layout=widgets.Layout(overflow_y="visible",
                                  align_content="stretch",
                                  justify_content="flex-start",)
        )
        panel_children.append(html_mesh_explainer)

        hbox_cellsize = build_widget_input_values_xyz_tuple(
            r"\(\Delta d\)", default=self._controls.cellsize
        )
        panel_children.append(hbox_cellsize)
        self.cell_x = hbox_cellsize.children[1]
        self.cell_y = hbox_cellsize.children[2]
        self.cell_z = hbox_cellsize.children[3]

    def _output_button_widgets(self, panel_children):
        """Buttons to initialise/reset the domain."""
        self.btn_init = widgets.Button(
            description="Initialise domain",
            style={"button_width": "auto",
                   "button_style": "info"},
        )
        self.btn_init.on_click(self._on_initialize)

        self.btn_reset = widgets.Button(
            description="Reset domain",
            style={"button_width": "auto",
                   "button_style": "info"},
            disabled=True,
        )

        self.btn_reset.on_click(self._on_reset)

        hbox_btns = widgets.HBox(
            [self.btn_init, self.btn_reset],
            layout=widgets.Layout(
                width='auto',
                height='auto',
                align_items="center",
                align_content="center",
                justify_content='space-around'
            )
        )
        panel_children.append(hbox_btns)

