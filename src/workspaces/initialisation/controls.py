#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ControlsPanel:
 - Outliner
 - Modelling tab (vertical ToggleButtons of regions)
 - Properties & Options
"""

import ipywidgets as widgets
from ipywidgets import Layout, GridspecLayout
from IPython.display import display
import discretisedfield as df
import logging
from .geometry import *
from .magnetisation import *
from src.config import *

logger = logging.getLogger(__name__)


__all__ = ["ControlsPanel"]


class ControlsPanel:
    def __init__(
            self,
            cellsize: type_aliases.UbermagCellsizeType,
            dims: type_aliases.UbermagDimsType,
            units: type_aliases.UbermagUnitsType
    ):
        # Brought in from builder
        self.cellsize, self.dims, self.units = cellsize, dims, units

        # Required to define mm.System
        self.main_region = None
        self.subregions   = {}
        self.mesh = None
        self.init_mag = None  # Temporary; should be stored directly in mm.System
        # listeners for external code
        self._mesh_listeners = []
        self._init_mag_listeners = []

        # 1) Outliner pane
        self.outliner_box = widgets.HTML(
            '<i>No domain set.</i>',
            layout=Layout(overflow='auto')
        )

        # 2) instantiate each initialisation panel
        self.panels_model = {
            'Domain': CreateDomain(),
            'Place':  PlaceRegionInModel(),
            # 'Divide': DividePanel(),
            'Append': AppendRegionToExisting(),
            'Remove': RemoveRegion()
        }

        self.panels_system_init = {
            'Mesh': DomainMesh(),
            'Initial fields': DefineSystemInitialMagnetisation(),
            'Subregions in mesh': SelectSubregionsInMesh(),
        }

        # 3) Build the three top‐level tabs
        self.model_tabs     = self._build_model_creation_panel(self.panels_model)
        self.system_init_tab = self._build_model_creation_panel(self.panels_system_init)
        self.options_tab    = self._build_options_tab()

        self.properties_pane = widgets.Tab(
            children=[self.model_tabs,
                      self.system_init_tab,
                      self.options_tab]
        )
        for i, title in enumerate(['Modelling','System Init.','Options']):
            self.properties_pane.set_title(i, title)

        # placeholders for callbacks
        self._plot_callback = None
        # for mesh‐creation callbacks
        self._mesh_listeners = []

    def register_plot_callback(self, plot_cb):
        """
        Called by builder to hand us the viewport's plot_regions.
        Also give each panel a state‐mutator and the plot callback.
        """
        self.register_model_callbacks(plot_cb)

    def register_model_callbacks(self, plot_cb):
        self._plot_callback = plot_cb

        # Domain panel → set main domain
        domain_panel = self.panels_model.get('Domain')
        if domain_panel:
            domain_panel.set_state_callback(self.set_domain)
            domain_panel.set_plot_callback(plot_cb)

        # PlaceRegionInModel → add new subregion
        place_panel = self.panels_model.get('Place')
        if place_panel:
            place_panel.set_state_callback(self.add_subregion)
            place_panel.set_plot_callback(plot_cb)

        # AppendRegion to existing -> add new subregion
        append_panel = self.panels_model.get('Append')
        if append_panel:
            append_panel.set_state_callback(self.add_subregion)
            append_panel.set_plot_callback(plot_cb)

        # RemoveRegion -> remove existing subregion
        remove_panel = self.panels_model.get('Remove')
        if remove_panel:
            remove_panel.set_state_callback(self.remove_subregion)
            remove_panel.set_plot_callback(plot_cb)

    def register_system_callbacks(self):
        """
        Hook up the MeshPanel and InitialMagnetisationPanel.
        on_mesh_created(mesh) will be called when a df.Mesh is ready.
        on_initial_magnetisation(field) will be called when m₀ is defined.
        """
        # Mesh panel → set main mesh in ControlsPanel
        mesh_panel = self.panels_system_init.get('Mesh')
        if mesh_panel:
            mesh_panel.set_state_callback(self._on_mesh_created)
        # Initial‑fields panel → set initial fields field
        init_mag_panel = self.panels_system_init.get('Initial fields')
        if init_mag_panel:
            init_mag_panel.set_state_callback(self._on_init_mag_created)

        subregions_panel = self.panels_system_init.get('Subregions in mesh')
        if subregions_panel:
            subregions_panel.set_state_callback(self._on_mesh_created)

    def _build_model_creation_panel(self, panel_ident):
        names = list(panel_ident.keys())

        # Guaranteeing widths are particularly helpful when displaying icons
        min_width = str(min(max(len(n) for n in names), 8) + 2) + "ch"

        selector = widgets.ToggleButtons(
            options=names,
            tooltips=tuple(names),
            button_style='',
            style={
                'button_width': min_width,
                'align_content': 'center',
                'justify_content': 'center'
            },
            layout=Layout(
                min_width=min_width,
                width='auto', height='100%',
                overflow='auto',
                display='flex', # required for column-nowrap to take effect
                flex_flow='column nowrap'
            ),
        )
        content = widgets.Output(layout=Layout(overflow='auto'))

        def _on_select(change):
            if change['name']=='value':
                content.clear_output()
                with content:
                    display(panel_ident[change['new']].build(self))
        selector.observe(_on_select, names='value')

        # explicit initial display call
        _on_select({'name':'value', 'new': names[0]})

        grid = GridspecLayout(n_rows=1, n_columns=2,
                              layout=Layout(width='100%', height='100%')
                              )
        grid._grid_template_columns = f'{min_width} 1fr'  # 1st column follows own Layout, and 2nd column fills remaining space
        grid.grid_gap = '4px'
        grid[0,0] = selector
        grid[0,1] = content
        return grid

    def _build_system_initiation_tab(self):
        names = list(self.panels_system_init.keys())
        width = str(min(max(len(n) for n in names), 8) + 2) + "ch"

        selector = widgets.ToggleButtons(
            options=names,
            orientation='vertical',
            layout=Layout(width=width, overflow='auto', height='100%'),
            style={'button_width': width}
        )
        content = widgets.Output(layout=Layout(overflow='auto', height='100%'))

        def _on_select(change):
            if change['name'] == 'value':
                content.clear_output()
                with content:
                    display(self.panels_system_init[change['new']].build(self))

        selector.observe(_on_select, names='value')

        # explicit initial display call
        _on_select({'name': 'value', 'new': names[0]})

        grid = GridspecLayout(n_rows=1, n_columns=2)
        grid._grid_template_columns = '25% 75%'
        grid.grid_gap = '4px'
        grid.layout.height = '100%'
        grid[0, 0] = selector
        grid[0, 1] = content
        return grid

    def _build_options_tab(self):
        """
        Build the Options tab: show/hide domain and units dropdown.
        """
        # 1) Show / hide domain toggle
        self.toggle_show = widgets.Checkbox(value=True, description='Show Domain')
        self.toggle_show.observe(lambda _: self._refresh_plot(), names='value')

        # 2) Units dropdown (must match your CreateDomain)
        self.units_dd = widgets.Dropdown(
            options=list(type_aliases.UNIT_FACTORS.keys()),
            value=self.units[0],
            description='Units:',
            layout=Layout(width='auto')
        )
        # whenever units change, relabel axes and re‐draw
        self.units_dd.observe(lambda _: self._refresh_plot(), names='value')

        return widgets.VBox(
            [self.toggle_show, self.units_dd],
            layout=Layout(overflow='auto', height='100%')
        )

    def build_header(self):
        """Header toggles for View / Workspace."""
        view = widgets.ToggleButtons(
            options=['3D view','2D view'],
            description='View:',
            layout=Layout(width='auto'),
            style={'button_width':'auto'}
        )
        workspace = widgets.ToggleButtons(
            options=['Modelling','Properties'],
            description='Workspace:',
            layout=Layout(width='auto'),
            style={'button_width':'auto'}
        )
        # switch top‐level tab on workspace change
        workspace.observe(
            lambda ch: setattr(
                self.properties_pane, 'selected_index',
                0 if ch['new']=='Modelling' else 1
            ),
            names='value'
        )
        return widgets.HBox(
            [view, workspace],
            layout=Layout(justify_content='flex-start')
        )

    def build(self):
        """Assemble Outliner + Properties into a 2×1 grid."""
        ctrl = GridspecLayout(n_rows=2, n_columns=1)
        ctrl.grid_gap = '4px'
        ctrl.layout.height = '100%'
        ctrl._grid_template_rows = '30% 70%'

        ctrl[0,0] = self.outliner_box
        ctrl[1,0] = self.properties_pane
        return ctrl

    # —— state mutators  ——
    def set_domain(self, region):
        self.main_region = region
        self.subregions.clear()
        self.update_outliner()
        self._refresh_plot()
        self._refresh_system_init()

    def add_subregion(self, name, region):
        self.subregions[name] = region
        self.update_outliner()
        self._refresh_plot()
        self._refresh_system_init()

    def remove_subregion(self, name):
        self.subregions.pop(name, None)
        self.update_outliner()
        self._refresh_plot()
        self._refresh_system_init()

    def update_outliner(self):
        """Re‐render the Outliner tree."""
        if not self.main_region:
            self.outliner_box.value = '<i>No domain set.</i>'
            return
        html = '<ul><li>main_region'
        for nm in self.subregions:
            html += f"<ul><li>{nm}</li></ul>"
        html += '</li></ul>'

        # If a mesh exists, show its cell counts:
        if self.mesh:
            # Mesh repr prints region & n—but you might prefer n directly:
            n = self.mesh.n
            html += f"<p><b>Mesh cells:</b> {n}</p>"

        # If an initial‐fields field exists, show its value & norm:
        if self.init_mag:
            val = self.init_mag.value      # e.g. (0,0,1)
            norm = getattr(self.init_mag, 'norm', None)
            html += "<p><b>Init mag:</b> " \
                    f"value={val}" + \
                    (f", norm={norm}" if norm is not None else "") + \
                    "</p>"

        self.outliner_box.value = html

    def _refresh_plot(self):
        """Re‐draw via the viewport callback."""
        if self._plot_callback:
            self._plot_callback(
                self.main_region,
                self.subregions,
                show_domain=self.toggle_show.value
            )

    def _refresh_system_init(self):
        """
        Keep the MeshPanel’s base‐region dropdown in sync.
        """
        mesh_panel = self.panels_system_init.get('Mesh')
        if not mesh_panel:
            return
        # bases = ['main'] + all subregion names, but only once main_region exists
        if self.main_region is None:
            mesh_panel.dd_base_region.options = []
            mesh_panel.dd_base_region.value = None
        else:
            bases = ['main'] + list(self.subregions.keys())
            mesh_panel.refresh(bases)

        init_mag_panel = self.panels_system_init.get("Initial fields")
        if not init_mag_panel:
            return
        if init_mag_panel is not None:
            init_mag_panel.refresh()

        subregions_panel = self.panels_system_init.get("Subregions in mesh")
        if not subregions_panel:
            return
        if subregions_panel is not None:
            subregions_panel.refresh()

    def refresh(self):
        """External API for builder to force a redraw of plots AND system panels."""
        self._refresh_plot()
        # keep the MeshPanel’s base-region dropdown in sync on startup
        self._refresh_system_init()

    def _on_mesh_created(self, mesh):

        logger.success("ControlsPanel received mesh: %r", mesh)
        # store the new mesh
        self.mesh = mesh

        # update the mesh dropdown in System‑Init tab
        self._refresh_system_init()
        # update outliners display
        self.update_outliner()
        # notify any registered external listeners
        for cb in self._mesh_listeners:
            cb(mesh)

    def _on_init_mag_created(self, field):
        """Called by DefineSystemInitialMagnetisation when m₀ is defined."""
        logger.success("ControlsPanel received m₀ field: %r", field)
        self.init_mag = field

        # update outliners (or other UI) as desired
        self.update_outliner()

        # notify external listeners
        for cb in self._init_mag_listeners:
            cb(field)

    def register_mesh_listener(self, cb):
        """ Builder (or anyone) can listen for new domain: cb(mesh). """
        self._mesh_listeners.append(cb)

    def register_init_mag_listener(self, cb):
        """
        Register an external listener to be called when initial fields is defined.
        """
        self._init_mag_listeners.append(cb)

