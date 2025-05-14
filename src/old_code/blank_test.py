#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AppendRegionUsingBase:
    Extrude a new subregion off a base region (main or existing).

Adapted to the new controller pattern:
 - no internal plot callback here (plotting is handled upstream)
 - only a state callback: cb(name: str, new_region: df.Region)
 - pulls dims, units, subregions, cellsize from the passed-in controller
"""

import ipywidgets as widgets
from ipywidgets import Layout
from src.helper_functions import create_scaled_region_from_base_region

__all__ = ["AppendRegionUsingBase"]


class AppendRegionUsingBase:
    def __init__(self):
        # callback to WorkspaceController.add_subregion(name, region)
        self._state_cb = None
        # will be set in build()
        self._controller = None

        # placeholders for widgets
        self.text_region_name = None
        self.dd_base = None
        self.tb_axis = None
        self.tb_side = None
        self.dd_scale_mode = None
        self.ftext_scale_amount = None
        self.btn_append = None

    def set_state_callback(self, cb):
        """
        Register the callback that accepts (name:str, region:df.Region).
        """
        self._state_cb = cb
        if self.btn_append is not None:
            # re-wire if button already exists
            self.btn_append.on_click(self._on_append)

    def build(self, controller) -> widgets.VBox:
        """
        Build and return the UI for appending a subregion.
        Capture controller so we can read dims/units and existing subregions.
        """
        self._controller = controller
        panel_children = []

        # 1) Explanation
        panel_children.append(
            widgets.HTML(
                value="Generate a new region by appending to an existing region.",
                layout=Layout(margin="0 0 8px 0")
            )
        )

        # 2) New-region name
        panel_children.append(
            widgets.HBox(
                [
                    widgets.HTML(value="New region"),
                    self.text_region_name := widgets.Text(
                        placeholder="name", layout=Layout(width="40%")
                    )
                ],
                layout=Layout(
                    width="auto", align_items="center", justify_content="flex-end", gap="4px"
                )
            )
        )

        # 3) Base-region dropdown
        bases = ["main"] + list(controller.subregions.keys())
        panel_children.append(
            widgets.HBox(
                [
                    widgets.HTML(value="Base region"),
                    self.dd_base := widgets.Dropdown(
                        options=bases, layout=Layout(width="40%")
                    )
                ],
                layout=Layout(
                    width="auto", align_items="center", justify_content="flex-end", gap="4px"
                )
            )
        )

        # 4) Orientation explainer
        panel_children.append(
            widgets.HTMLMath(
                value="To set the orientation of the generated region provide:",
                layout=Layout(margin="8px 0 0 0")
            )
        )

        # axis selector
        panel_children.append(
            widgets.HBox(
                [
                    widgets.HTML(value="Cartesian axis"),
                    self.tb_axis := widgets.ToggleButtons(
                        options=[("x", "x"), ("y", "y"), ("z", "z")],
                        style={"button_width": "auto"}
                    )
                ],
                layout=Layout(
                    width="auto", align_items="center", justify_content="flex-end", gap="4px"
                )
            )
        )

        # side selector
        panel_children.append(
            widgets.HBox(
                [
                    widgets.HTML(value="Face along"),
                    self.tb_side := widgets.ToggleButtons(
                        options=[("+ve", "max"), ("-ve", "min")],
                        style={"button_width": "auto"}
                    )
                ],
                layout=Layout(
                    width="auto", align_items="center", justify_content="flex-end", gap="4px"
                )
            )
        )

        # 5) Scaling controls
        panel_children.extend(self._make_scaling_controls())

        # 6) Append button
        panel_children.append(
            widgets.HBox(
                [
                    self.btn_append := widgets.Button(
                        description="Append region",
                        layout=Layout(width="auto"),
                        style={"button_width": "auto"}
                    )
                ],
                layout=Layout(justify_content="center", margin="12px 0")
            )
        )
        if self._state_cb:
            self.btn_append.on_click(self._on_append)

        # wrap in a VBox
        return widgets.VBox(
            panel_children,
            layout=Layout(overflow="auto", padding="4px")
        )

    def _on_append(self, _):
        """When user clicks 'Append'—compute and fire state callback."""
        name = self.text_region_name.value.strip()
        if not name:
            self.btn_append.button_style = "danger"
            return

        # gather inputs
        base_key     = self.dd_base.value
        axis         = self.tb_axis.value
        side         = self.tb_side.value
        scale_mode   = self.dd_scale_mode.value
        scale_amount = self.ftext_scale_amount.value

        # lookup parent region
        parent = (
            self._controller.main_region
            if base_key == "main"
            else self._controller.subregions.get(base_key)
        )
        if parent is None:
            self.btn_append.button_style = "danger"
            return

        # compute new Region (all SI internally)
        new_region = create_scaled_region_from_base_region(
            base_region=parent,
            scale_amount=scale_amount,
            cellsize=self._controller.cellsize,
            reference_side=side,
            scale_along_axis=axis,
            scale_is_absolute=(scale_mode == "absolute")
        )

        # notify workspace controller
        if self._state_cb:
            self._state_cb(name, new_region)

    def _make_scaling_controls(self):
        """
        Returns [ explainer HTMLMath, HBox( Dropdown + Stack ) ]
        using controller.cellsize and controller.units.
        """
        ctrl = self._controller
        # explainer
        expl = widgets.HTMLMath(
            value="Define how the new region will be scaled:",
            layout=Layout(margin="8px 0 0 0")
        )

        # dropdown
        modes = [("Relative", "relative"), ("Absolute", "absolute")]
        max_label = max(len(m) for m, _ in modes)
        dd_width = f"{max_label*1.5 + 2}ch"
        self.dd_scale_mode = widgets.Dropdown(
            options=modes, value="relative", layout=Layout(width=dd_width)
        )

        # FloatText
        self.ftext_scale_amount = widgets.FloatText(
            placeholder=1, layout=Layout(width="4rem")
        )

        # explanatory boxes
        axis_map = {"x": 0, "y": 1, "z": 2}
        ax = axis_map[self.tb_axis.value]
        cell = ctrl.cellsize[ax]
        unit = ctrl.units[ax]

        box_rel = widgets.HTMLMath(
            value=rf"unit cells where Δd_{{{self.tb_axis.value}}} = {cell}",
            layout=Layout(overflow_x="visible")
        )
        box_abs = widgets.HTMLMath(value=f"{unit}")

        h_rel = widgets.HBox([self.ftext_scale_amount, box_rel],
                             layout=Layout(align_items="center", gap="4px"))
        h_abs = widgets.HBox([self.ftext_scale_amount, box_abs],
                             layout=Layout(align_items="center", gap="4px"))

        stack = widgets.Stack(
            children=[h_rel, h_abs],
            selected_index=0,
            layout=Layout(width="auto")
        )
        widgets.jslink((self.dd_scale_mode, "index"), (stack, "selected_index"))

        return [expl, widgets.HBox([self.dd_scale_mode, stack],
                                  layout=Layout(align_items="center", gap="4px"))]