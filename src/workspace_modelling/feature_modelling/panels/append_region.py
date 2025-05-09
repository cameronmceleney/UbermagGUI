#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AppendRegionToExisting:
    Extrude a new subregion off a base region (main or existing).
"""

import ipywidgets as widgets
from ipywidgets import Layout
from helper_functions import (
    create_scaled_region_from_base_region,
)

__all__ = ["AppendRegionToExisting"]


class AppendRegionToExisting:
    def __init__(self):
        # callbacks to ControlsPanel
        self._state_cb   = None     # ControlsPanel.add_subregion
        self._plot_cb    = None     # ViewportArea.plot_regions
        self._controls   = None     # set at build()

        # widgets (will be re-created each build)
        self.text_region_name = None
        self.dd_base = None
        self.tb_axis = None
        self.tb_side = None
        self.dd_scale_mode = None
        self.ftext_scale_amount = None
        self.btn_append = None

    def set_state_callback(self, cb):
        """Register ControlsPanel.add_subregion."""
        self._state_cb = cb

    def set_plot_callback(self, cb):
        """Register ViewportArea.plot_regions."""
        self._plot_cb = cb

        if self.btn_append:
            self.btn_append.on_click(self._on_append)

    def build(self, controls_panel):
        """
        Build and return the UI for appending a subregion.
        Capture controls_panel so we can read dims/units and existing subregions.
        """
        self._controls = controls_panel
        # Dynamically collect children
        append_panel = widgets.VBox(
            layout=Layout(
                width='auto',
                height='auto',
                overflow="auto",
                padding="4px"
            ),
        )
        panel_children = []

        # 1) Explanation HTML about purpose of panel
        html_explainer_region = widgets.HTML(
            value="Generate a new region by appending to an existing region.",
            layout=widgets.Layout(
                width='auto',
            )
        )
        panel_children.append(html_explainer_region)

        html_region_name = widgets.HTML(
            value="New region",
        )
        self.text_region_name = widgets.Text(
            placeholder="name",
            layout=Layout(width='40%'),
        )
        hbox_region_name = widgets.HBox(
            children=[html_region_name, self.text_region_name],
            layout=Layout(
                width='auto',
                height='auto',
                align_items='center',
                align_content='center',
                justify_content='flex-end',
            )
        )
        panel_children.append(hbox_region_name)

        html_base_name = widgets.HTML(
            value="Base region",
        )
        bases = ["main"] + list(controls_panel.subregions.keys())
        self.dd_base = widgets.Dropdown(
            options=bases,
            layout=Layout(width="40%")
        )
        hbox_dd_base = widgets.HBox(
            children=[html_base_name, self.dd_base],
            layout=Layout(
                width='auto',
                height='auto',
                align_items='center',
                align_content='center',
                justify_content='flex-end',
            )
        )
        panel_children.append(hbox_dd_base)

        ####
        html_orientation_explainer = widgets.HTMLMath(
            value=(
                "To set the orientation of the generated region provide: "
            ),
            layout=widgets.Layout(overflow_y="visible", width="auto")
        )
        panel_children.append(html_orientation_explainer)

        # 2) Axis selector (x, y or z)
        html_axis = widgets.HTML(
            value="Cartesian axis ",
        )
        self.tb_axis = widgets.ToggleButtons(
            options=[("x", "x"), ("y", "y"), ("z", "z")],
            style={"button_width": "auto"},
        )

        hbox_axis = widgets.HBox(
            children=[html_axis, self.tb_axis],
            layout=Layout(
                width='auto',
                height='auto',
                align_content='stretch',
                justify_content='flex-end',
            )
        )
        panel_children.append(hbox_axis)

        # 3) Side selector (positive or negative face)
        html_side = widgets.HTML(
            value="face aligned along "
        )

        self.tb_side = widgets.ToggleButtons(
            options=[("+ve", "max"), ("-ve", "min")],
            style={"button_width": "auto"}
        )

        hbox_side = widgets.HBox(
            children=[html_side, self.tb_side],
            layout=Layout(
                width='auto',
                height='auto',
                align_content='stretch',
                justify_content='flex-end'
            )
        )

        panel_children.append(hbox_side)

        # 4) Explain how scaling works to user
        self._length_scaling_widgets(panel_children)

        # 5) Append button handling already created in __init__; just need to create button for signalling
        self.btn_append = widgets.Button(
            description='Append region',
            layout=Layout(width='auto'),
            style={'button_width': 'auto'}
        )
        self.btn_append.on_click(self._on_append)
        btn_box = widgets.HBox(
            [self.btn_append],
            layout=Layout(justify_content='center', width='100%')
        )
        panel_children.append(btn_box)

        append_panel.children = tuple(panel_children)
        return append_panel

    def refresh(self, bases):
        """Public API to refresh the list of existing regions."""
        self._refresh()

    def _refresh(self):
        if self._plot_cb:
            self._plot_cb(
                self._controls.main_region,
                self._controls.subregions,
                self._controls.toggle_show.value
            )

    def _on_append(self, _):
        """
        When user clicks 'Append':
          1. convert inputs to SI
          2. slice & scale slab
          3. register new region via state callback
          4. redraw via plot callback
        """
        region_name = self.text_region_name.value.strip()
        if not region_name or region_name is None:
            self.btn_append.button_style = 'danger'
            return

        try:
            base_key = self.dd_base.value
            axis     = self.tb_axis.value
            side     = self.tb_side.value
            scale_mode = self.dd_scale_mode.value
            scale_amount = self.ftext_scale_amount.value

            # lookup the parent region (main or subregion)
            parent = (
                self._controls.main_region
                if base_key == "main"
                else self._controls.subregions.get(base_key)
            )
            if parent is None:
                self.btn_append.button_style = 'success'
                return

            # compute new Region (all SI internally)
            new_region = create_scaled_region_from_base_region(
                base_region=parent,
                scale_amount=scale_amount,
                cellsize=self._controls.cellsize,
                reference_side=side,
                scale_along_axis=axis,
                scale_is_absolute=(scale_mode == "absolute")
            )

        except Exception as e:
            self.btn_append.button_style = 'danger'
            raise f"AppendRegionToExisting failed: {e}"

        # 1) notify ControlsPanel
        if self._state_cb:
            self._state_cb(region_name, new_region)

        # 2) redraw the Viewport
        self._refresh()

    def _length_scaling_widgets(self, panel_children: list):

        # Explain to the user how the scaling works
        html_scale_explainer = widgets.HTMLMath(
            value=(
                f"Define how the new region will be scaled. "
            ),
            layout=widgets.Layout(overflow_y="visible", width="auto")
        )
        panel_children.append(html_scale_explainer)

        # scale_mode_options must be compatible with helper_functions!
        scale_mode_options = [("Relative", "relative"), ("Absolute", "absolute")]
        max_label_length = max(len(label) for label, _ in scale_mode_options)
        dd_width = f"{max_label_length*1.5 + 2}ch"
        self.dd_scale_mode = widgets.Dropdown(
            options=scale_mode_options,
            value='relative',
            layout=Layout(width=dd_width)
        )

        # 3) FloatText for the amount (shared by both modes)
        self.ftext_scale_amount = widgets.FloatText(
            placeholder=1,
            layout=Layout(width="4rem")  # wide enough for “10000”
        )

        # 4) Build the mode‐specific HBoxes that Stack will rotate through
        axis_map = {"x": 0, "y": 1, "z": 2}
        ax = axis_map[self.tb_axis.value]

        # 4a) Relative (unit‐cells) box
        html_rel = widgets.HTMLMath(
            value=(
                r"unit cells where<br>"
                rf"\(\Delta d_{{{self.tb_axis.value}}} = {self._controls.cellsize[ax]}\)"
                f" {self._controls.units[ax]}"
            ),
            layout=Layout(width="auto", overflow_x='visible')
        )
        hbox_rel = widgets.HBox(
            [self.ftext_scale_amount, html_rel],
            layout=Layout(align_items="center", gap="4px")
        )

        # 4b) Absolute (distance) box
        html_abs = widgets.HTMLMath(
            value=f"{self._controls.units[ax]}",
            layout=Layout(width="auto")
        )
        hbox_abs = widgets.HBox(
            [self.ftext_scale_amount, html_abs],
            layout=Layout(align_items="center", gap="4px")
        )

        # 5) Stack them and hook up the dropdown
        stack_length_scaling = widgets.Stack(
            children=[hbox_rel, hbox_abs],
            selected_index=0,
            layout=Layout(width="auto")
        )

        widgets.jslink((self.dd_scale_mode, 'index'), (stack_length_scaling, 'selected_index'))

        # 6) Finally put dropdown + stack side by side
        hbox_dropdown_plus_stack = widgets.HBox(
            [self.dd_scale_mode, stack_length_scaling],
            layout=Layout(width="auto", height="auto", align_items="center", gap="4px")
        )

        panel_children.append(hbox_dropdown_plus_stack)

