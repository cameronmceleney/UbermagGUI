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

# Standard library imports
import ipywidgets as widgets
from IPython.display import display
import logging

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
    def __init__(self, system, dims, units):
        """
        Parent abstract class to help with buildings features that controllers will manage.
        """
        # Shared context for all panels
        self.system = system
        self.dims = dims
        self.units = units

        # Filled in by build_feature()
        self.panels = {}
        self.selector: widgets.ToggleButtons = widgets.ToggleButtons()
        self.content: widgets.Output = widgets.Output(layout=widgets.Layout(overflow="auto"))

    def build_feature(self, panel_map: dict) -> widgets.GridspecLayout:
        """
        Build a two-column layout for the given panels:
            - a ToggleButtons column on the left
            - a content Output area on the right to host 'features'

        panel_map: mapping from tab‐name to panel‐instance (must support .build(self))
        """
        # Stash for children
        self.panels = panel_map

        self._build_toggles_with_wiring()

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

        return grid

    def _build_toggles_with_wiring(self):
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
        self.selector = selector

        # Initialise to first tab
        self.selector.value = names[0]

    def _on_select(self, change: dict):
        if change.get('name') == 'value':
            panel = self.panels[change['new']]
            self.content.clear_output()
            with self.content:
                display(panel.build(self))


class GeometryController(HandleFeature):
    def __init__(
            self,
            system,
            plot_callback,
            dims,
            units,
            domain_callback,
            add_callback,
            remove_callback,
    ):
        super().__init__(system, dims, units)

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
            system, dims, units,
            mesh_callback,
            init_mag_callback
            ):
        super().__init__(system, dims, units)

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

    def build(self) -> widgets.GridspecLayout:
        return self.build_feature(self.panels)

    def refresh_mesh_dropdown(self):
        """
        Helper to keep the base-region dropdown in sync whenever subregions change.
        """
        mesh_panel = self.panels.get("Mesh")
        if not mesh_panel:
            return

        if self.system.main_region is None:
            mesh_panel.dd_base_region.options = []
            mesh_panel.dd_base_region.value = None
        else:
            bases = ["main"] + list(self.system.subregions.keys())
            mesh_panel.refresh(bases)


class InitialisationController:
    """
    Exposes Geometry + System‐Init features under one Tab widget.
    """
    def __init__(
            self,
            system, dims, units,
            # callbacks from top‐level WorkspaceController:
            plot_callback,
            domain_callback,
            add_callback,
            remove_callback,
            mesh_callback,
            init_mag_callback,
    ):
        # instantiate each feature now that dims/units are known
        self.geometry = GeometryController(
            system=system,
            dims=dims, units=units,
            plot_callback=plot_callback,
            domain_callback=domain_callback,
            add_callback=add_callback,
            remove_callback=remove_callback,
        )

        self.system_init = SystemInitController(
            system=system,
            dims=dims, units=units,
            mesh_callback=mesh_callback,
            init_mag_callback=init_mag_callback,
        )

        # wire up after-mesh changes
        self.system_init.panels['Mesh'].set_state_callback(mesh_callback)
        self.system_init.panels['Initial fields'].set_state_callback(init_mag_callback)
        self.system_init.panels['Subregions in mesh'].set_state_callback(mesh_callback)

        # assemble into a Tab
        self.tab = widgets.Tab(
            children=[self.geometry.build(), self.system_init.build()],
            layout=widgets.Layout(width='100%', height='100%')
        )

        self.tab.set_title(0, "Geometry")
        self.tab.set_title(1, "System Init.")

    def build(self):
        """
        Called by WorkplaceController.render().

        Returns our wired tab.
        """
        return self.tab
