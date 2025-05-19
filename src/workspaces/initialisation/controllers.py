#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Project: UbermagGUI
Path:    src/workspaces/initialisation/controllers.py

InitialisationController:
    Bundles GeometryController & SystemInitController under a Tab.

GeometryController:
    Hosts the “Domain / Place / Append / Remove” panels.
    Formerly self.panels_model + _build_model_creation_panel.

SystemInitController:
    Hosts the “Mesh / Initial fields / Subregions” panels.
    Formerly self.panels_system_init + _build_system_initiation_tab.

HandleFeature:
    Abstract base to build a toggle-selector + content region for a group of panels.

Author:      Cameron Aidan McEleney < c.mceleney.1@research.gla.ac.uk >
Created:     12 May 2025
IDE:         PyCharm
Version:     0.1.0
"""
from __future__ import annotations

# Standard library imports
import ipywidgets as widgets
from IPython.display import display
import logging
import typing

# Third-party imports
import discretisedfield as df

# Local application imports
from . import domain, regions, fields, meshes

logger = logging.getLogger(__name__)


__all__ = [
    "HandleFeature",
    "GeometryController",
    "SystemInitController",
    "InitialisationController"
]


class HandleFeature:
    def __init__(
            self,
            properties_controller
    ):
        """
        Parent abstract class to help with buildings features that controllers will manage.
        """
        # Live states come from workspace_controller.py inheritance
        # Live states come from builder.py/UbermagInterface inheritance
        self._props_controller = properties_controller
        # Filled in by build_feature() of each feature controller
        self.panels = {}
        self.selector: widgets.ToggleButtons = widgets.ToggleButtons()
        self.panels_container: widgets.Box = widgets.Box()  # TODO. Get working
        self.content: widgets.Output = widgets.Output(
            layout=widgets.Layout(width='100%', height='100%', min_height='0', overflow_x="hidden", overflow_y='auto'))

    def build_feature(self, panel_map: dict) -> widgets.GridspecLayout:
        """
        Build a two-column layout for the given panels:
            - a ToggleButtons column on the left
            - a content Output area on the right to host 'features'

        panel_map: mapping from tab‐name to panel‐instance (must support .build(self))
        """
        # Stash for children
        self.panels = panel_map
        # Rebuilt toggles and initialise to first tab
        self.selector = self._build_toggles_with_wiring()

        # Build feature
        grid = widgets.GridspecLayout(
            n_rows=1, n_columns=2,
            layout=widgets.Layout(
                width='100%',
                height='100%',
                gap='4px',
            )
        )

        # 1st column follows own Layout, and 2nd column fills remaining space
        grid._grid_template_columns = f'{self.selector.style.button_width} 1fr'

        grid[0, 0] = self.selector
        grid[0, 1] = self.content

        # — render the initially‐selected panel immediately —
        first = self.selector.value
        panel = self.panels[first]
        with self.content:
            display(panel.build(self._props_controller))

        return grid

    def _build_toggles_with_wiring(self) -> widgets.ToggleButtons:
        """
        Construct the ToggleButtons used to change between panels of this feature, and setup the
        wiring required by `workspace_controller.py` and other higher-level controllers.
        """
        names = list(self.panels.keys())

        # Guaranteeing widths will be particularly helpful when displaying icons
        min_width = '10ch' #str(min(max(len(n) for n in names), 8) + 2) + "ch"

        selector = widgets.ToggleButtons(
            options=names,
            tooltips=tuple(names),
            button_style='',
            style={
                'button_width': min_width,
                'align_content': 'center',
                'justify_content': 'center'
            },
            layout=widgets.Layout(
                min_width=min_width,
                width='auto', height='100%',
                overflow='auto',
                display='flex',  # required for column-nowrap to take effect
                flex_flow='column nowrap'
            ),
        )

        selector.observe(self._on_select, names='value')

        selector.value = names[0]

        return selector

    def _on_select(self, change: dict):
        if change.get('name') == 'value':
            panel = self.panels[change['new']]
            self.content.clear_output()
            with self.content:
                # pass the workspace‐controller as context
                display(panel.build(self._props_controller))


class GeometryController(HandleFeature):
    def __init__(
            self,
            properties_controller,
            domain_callback,
            add_callback,
            remove_callback,
    ):
        super().__init__(properties_controller)

        # All panels in feature
        self.panels = {
            'Domain': domain.DefineDomainRegion(),
            'Place':  regions.PlaceRegion(),
            'Append': regions.AppendRegionUsingBase(),
            'Remove': regions.RemoveRegion()
        }

        self.panels['Domain'].set_state_callback(domain_callback)
        self.panels['Place'].set_state_callback(add_callback)
        self.panels['Append'].set_state_callback(add_callback)
        self.panels['Remove'].set_state_callback(remove_callback)

    def build(self) -> widgets.GridspecLayout:
        return self.build_feature(self.panels)


class SystemInitController(HandleFeature):
    def __init__(
            self,
            properties_controller,
            workspace_controller,
            mesh_callback,
            init_mag_callback,
            ):
        super().__init__(properties_controller)

        # panels for each step
        self.panels = {
            'Mesh': meshes.CreateMesh(),
            'Initial fields': fields.DefineSystemInitialMagnetisation(),
            'Subregions in mesh': meshes.SelectSubregionsInMesh()
        }

        # wire their state callbacks
        self.panels['Mesh'].set_state_callback(mesh_callback)
        self.panels['Initial fields'].set_state_callback(init_mag_callback)
        self.panels['Subregions in mesh'].set_state_callback(mesh_callback)

        # *** subscribe to geometry/mesh changes so dropdowns stay in sync ***
        # whenever a region is defined or removed:
        workspace_controller.register_geometry_listener(
            lambda main, subs: self.panels['Mesh'].refresh(
                list(subs.keys())
            )
        )

        # whenever a mesh is built or rebuilt:
        workspace_controller.register_mesh_listener(
            lambda mesh: (self.panels['Initial fields'].refresh(),
                          self.panels['Subregions in mesh'].refresh()
                          )
        )

        # TODO. Fix the horrid refresh arg.
        workspace_controller.register_mesh_listener(
            lambda mesh: self.panels['Mesh'].refresh(
                ['main'] + [n for n in self._props_controller.regions if n != 'main']
            )
        )

    def build(self) -> widgets.GridspecLayout:
        return self.build_feature(self.panels)


class InitialisationController:
    """
    Exposes Geometry + System‐Init features under one Tab widget.
    """
    def __init__(
            self,
            # access to top-level shared attributes
            properties_controller,
            workspace_controller,
            # callbacks from top‐level WorkspaceController:
            domain_callback,
            add_callback,
            remove_callback,
            mesh_callback,
            init_mag_callback,
    ):
        # instantiate each feature; wired handled by feature's controller
        self.geometry = GeometryController(
            properties_controller=properties_controller,
            domain_callback=domain_callback,
            add_callback=add_callback,
            remove_callback=remove_callback,
        )

        self.system_init = SystemInitController(
            properties_controller=properties_controller,
            workspace_controller=workspace_controller,
            mesh_callback=mesh_callback,
            init_mag_callback=init_mag_callback,
        )

    def build(self) -> widgets.Tab:
        """
        Called by WorkplaceController.render().

        Returns our wired tab.
        """
        tab = widgets.Tab(
            children=[self.geometry.build(), self.system_init.build()],
            layout=widgets.Layout(
                width='100%', height='100%'
            )
        )

        tab.set_title(0, "Geometry")
        tab.set_title(1, "System Init.")

        return tab
