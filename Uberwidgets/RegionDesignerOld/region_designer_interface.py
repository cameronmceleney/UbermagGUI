#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Project: Ubermag
Path:    include/Uberwidgets/region_designer_interface/region_designer_interface.py

Description:
    Redesigned GUI using GridspecLayout:
      - Header row (15%) with auto‐sized ToggleButtons
      - Body row (70%) with two columns: 3D viewport (left, 55%) and
        control feature_modelling (right, 45%)
      - Footer row (15%) with Instantiate button
    Control feature_modelling subdivided via nested Gridspec:
      - Outliner (30%) above Modelling feature_modelling (70%) implemented
        as vertical ToggleButtons + Output grid
    Viewport subdivided into plot (90%) and toolbar (10%).

Author:      Cameron Aidan McEleney <c.mceleney.1@research.gla.ac.uk>
Created:     28 Apr 2025
Version:     0.7.4
"""

from IPython.display import display
import ipywidgets as widgets
from ipywidgets import Layout, GridspecLayout
import numpy as np
import plotly.graph_objs as go
from plotly.graph_objs import FigureWidget
import discretisedfield as df

# Unit conversion factors to meters
_UNIT_FACTORS = {'m':1.0, 'um':1e-6, 'nm':1e-9}


def scaling_function(region: df.Region, sf: float, cellsize: tuple, side: str = 'max') -> df.Region:
    dims, units = region.dims, region.units
    if side in ['max', '+ve', 'positive']:
        p1 = (region.pmax[0], region.pmin[1], region.pmin[2])
        p2 = (region.pmax[0] + cellsize[0], region.pmax[1], region.pmax[2])
    elif side in ['min', '-ve', 'negative']:
        p1 = (region.pmin[0] - cellsize[0], region.pmin[1], region.pmin[2])
        p2 = (region.pmin[0], region.pmax[1], region.pmax[2])
    else:
        raise ValueError(f'Invalid side: was passed [{side}]')
    slab = df.Region(p1=p1, p2=p2, dims=dims, units=units)
    scaled = slab.scale((sf,1,1), reference_point=slab.pmin, inplace=False)
    new_pmin = tuple(round(v,9) for v in scaled.pmin)
    new_pmax = tuple(round(v,9) for v in scaled.pmax)
    return df.Region(p1=new_pmin, p2=new_pmax, dims=dims, units=units)


class RegionDesigner:
    """
    Interface using GridspecLayout and vertical ToggleButtons for modelling controls.
    """
    def __init__(self,
                 cellsize=(2e-9,1e-9,12e-9),
                 dims=('x','y','z'),
                 units=('m','m','m'),
                 show_borders=False):
        # State
        self.cellsize = cellsize
        self.dims = dims
        self.units = units
        self.main_region = None
        self._subregions = {}
        self.last_added = None
        self.show_borders = show_borders

        # Build UI
        self._make_header()
        self._make_viewport()
        self._make_controls()
        self._make_footer()

        # Main layout: 3 rows × 2 cols
        grid = GridspecLayout(
            n_rows=3, n_columns=2)
        grid.layout.min_width = '650px'
        grid.layout.min_width = '800px'
        grid.layout.height = 'auto'
        grid.layout.width = 'auto'
        grid._grid_template_rows = '15% 70% 15%'
        grid._grid_template_columns = '55% 45%'
        grid.grid_gap = '4px'

        # Header spans both cols
        grid[0, :] = self.header

        # Viewport area: left side
        vp_grid = GridspecLayout(
            n_rows=2,
            n_columns=1)
        vp_grid._grid_template_rows = '90% 10%'
        vp_grid.grid_gap = '2px'
        vp_grid.layout.height = 'auto'

        fig_box = widgets.Box([self.fig], layout=Layout(flex='1 1 auto', overflow='hidden'))
        vp_grid[0,0] = fig_box
        vp_grid[1,0] = self.vp_toolbar
        grid[1,0] = vp_grid

        # Controls right
        ctrl_grid = GridspecLayout(
            n_rows=2,
            n_columns=1)
        ctrl_grid._grid_template_rows='30% 70%'
        ctrl_grid.grid_gap='4px'
        ctrl_grid.height='auto'
        ctrl_grid[0,0] = self.outliner_box
        ctrl_grid[1,0] = self.properties_pane
        grid[1,1] = ctrl_grid

        # Footer spans both cols
        grid[2, :] = self.footer

        # Optional borders
        if self.show_borders:
            for pane in (self.header, vp_grid, ctrl_grid, self.footer):
                pane.layout.border = '1px solid gray'
                for child in pane.children:
                    child.layout.border = '1px solid red'

        display(grid)

        # Initialize content
        self._update_plot()
        self._update_outliner()
        # Default workspace and panel
        self.properties_pane.selected_index = 0
        self.workspace.value = 'Modelling'

    @property
    def subregions(self):
        return self._subregions

    @property
    def mesh(self):
        if not self.main_region:
            return None
        return df.Mesh(region=self.main_region,
                       cell=self.cellsize,
                       subregions=self._subregions)

    # UI builders
    def _make_header(self):
        self.view = widgets.ToggleButtons(
            options=['3D view','2D view'],
            description='View:',
            layout=Layout(width='auto'),
            style={'button_width':'auto'}
        )
        self.workspace = widgets.ToggleButtons(
            options=['Modelling','Properties'],
            description='Workspace:',
            layout=Layout(width='auto'),
            style={'button_width':'auto'}
        )
        self.workspace.observe(self._on_workspace, names='value')
        self.header = widgets.HBox(
            [self.view, self.workspace],
            layout=Layout(justify_content='flex-start')
        )

    def _make_viewport(self):
        cam = dict(eye=dict(x=-1.25,y=-1.25,z=1.25))
        self.fig = FigureWidget(
            layout=go.Layout(scene=dict(aspectmode='manual', camera=cam),
                              uirevision='camera', autosize=True)
        )
        self.vp_toolbar = widgets.HBox(
            [widgets.Button(description='Reset Camera',
                            layout=Layout(width='auto'),
                            style={'button_width':'auto'})],
            layout=Layout(justify_content='flex-start')
        )

    def _make_controls(self):
        # Outliner pane
        self.outliner_box = widgets.HTML(
            '<i>No domain set.</i>', layout=Layout(overflow='auto')
        )

        # Build modelling feature_modelling
        panels = {}
        # Domain panel
        t_pmin = widgets.Text(description='pmin (x,y,z):', placeholder='0,0,0')
        t_pmax = widgets.Text(description='pmax (x,y,z):')
        b_dom = widgets.Button(description='Initialize Domain', layout=Layout(width='auto'), style={'button_width':'auto'})
        b_dom.on_click(self.on_set_domain)
        panels['Domain'] = widgets.VBox([t_pmin,t_pmax,b_dom], layout=Layout(overflow='auto'))
        self._t_pmin, self._t_pmax = t_pmin, t_pmax
        # Place panel
        t_name = widgets.Text(description='Name:')
        t_ppmin = widgets.Text(description='pmin (x,y,z):')
        t_ppmax = widgets.Text(description='pmax (x,y,z):')
        b_place = widgets.Button(description='Place Region', layout=Layout(width='auto'), style={'button_width':'auto'})
        b_place.on_click(self.on_place)
        panels['Place'] = widgets.VBox([t_name,t_ppmin,t_ppmax,b_place], layout=Layout(overflow='auto'))
        self._t_name, self._t_ppmin, self._t_ppmax = t_name, t_ppmin, t_ppmax
        # Divide panel
        dd_div = widgets.Dropdown(options=[], description='Base:')
        chk_axes = widgets.HBox([widgets.Checkbox(value=True, description='X-axis'), widgets.Checkbox(value=False, description='Y-axis'), widgets.Checkbox(value=False, description='Z-axis')])
        t_divn = widgets.Text(description='Name:')
        f_divsf = widgets.FloatText(1.0, description='Scale:')
        b_div = widgets.Button(description='Divide', layout=Layout(width='auto'), style={'button_width':'auto'})
        b_div.on_click(self.on_divide)
        panels['Divide'] = widgets.VBox([dd_div,chk_axes,t_divn,f_divsf,b_div], layout=Layout(overflow='auto'))
        self._dd_div, self._t_divn, self._f_divsf = dd_div, t_divn, f_divsf
        # Append panel
        dd_app = widgets.Dropdown(options=[], description='Base:')
        tb = widgets.ToggleButtons(options=['min','max'], description='Side:', layout=Layout(width='auto'))
        # uniform width based on longest key
        max_label = max(len(k) for k in panels.keys())
        tb.layout.width = f'{max_label+2}ch'
        extrude = widgets.HBox([widgets.Checkbox(value=True,description='x'),widgets.Checkbox(False,description='y'),widgets.Checkbox(False,description='z')])
        t_appn = widgets.Text(description='Name:')
        f_appsf = widgets.FloatText(1.0, description='Scale:')
        b_app = widgets.Button(description='Append', layout=Layout(width='auto'), style={'button_width':'auto'})
        b_app.on_click(self.on_append)
        panels['Append'] = widgets.VBox([dd_app,tb,widgets.HTML('<b>Extrude along:</b>'),extrude,t_appn,f_appsf,b_app], layout=Layout(overflow='auto'))
        self._dd_app, self._tb_side, self._t_appn, self._f_appsf = dd_app, tb, t_appn, f_appsf
        # Remove panel
        dd_rem = widgets.Dropdown(options=[], description='Region:')
        b_rem = widgets.Button(description='Delete Region', layout=Layout(width='auto'), style={'button_width':'auto'})
        b_rem.on_click(self.on_remove)
        panels['Remove'] = widgets.VBox([dd_rem,b_rem], layout=Layout(overflow='auto'))
        self._dd_rem = dd_rem

        # ToggleButtons selector with uniform width
        names = list(panels.keys())
        width = f'{max(len(n) for n in names)+2}ch'
        self.model_selector = widgets.ToggleButtons(
            options=names,
            orientation='vertical',
            layout=Layout(width=width, overflow='auto', height='100%'),
            style={'button_width': width}
        )

        # Output area
        self.model_output = widgets.Output(layout=Layout(overflow='auto', height='100%'))

        def _on_select(change):
            if change['name']=='value':
                self.model_output.clear_output()
                with self.model_output:
                    display(panels[change['new']])
        self.model_selector.observe(_on_select)

        # trigger initial panel
        self.model_selector.value = names[0]
        _on_select({'name':'value','new':names[0]})

        # Grid: selector | content
        self.model_tabs = GridspecLayout(
            n_rows=1,
            n_columns=2)
        self.model_tabs._grid_template_columns='25% 75%'
        self.model_tabs.grid_gap='4px'
        self.model_tabs.layout.height = 'auto'
        self.model_tabs[0,0] = self.model_selector
        self.model_tabs[0,1] = self.model_output

        # Properties pane assembly
        placeholder = widgets.HTML('<b>Under development</b>')
        self.toggle_show = widgets.Checkbox(value=True, description='Show Domain')
        self.toggle_show.observe(lambda _:self._update_plot(), names='value')
        self.units_dd = widgets.Dropdown(options=['m','um','nm'], value=self.units[0], description='Units:')
        options_pane = widgets.VBox([self.toggle_show, self.units_dd], layout=Layout(overflow='auto'))
        self.properties_pane = widgets.Tab(children=[self.model_tabs, placeholder, options_pane])
        for i,title in enumerate(['Modelling','Properties','Options']):
            self.properties_pane.set_title(i, title)

    def _make_footer(self):
        self.btn_instant = widgets.Button(description='Instantiate', layout=Layout(width='auto'), style={'button_width':'auto'})
        self.btn_instant.on_click(self.on_instantiate)
        self.footer = widgets.HBox([self.btn_instant])

    # Internal helpers
    def _convert(self, vals):
        f = _UNIT_FACTORS[self.units_dd.value]
        return tuple(v * f for v in vals)

    def _plot_region(self, region, name, opacity):
        pmin, pmax = region.pmin, region.pmax
        pts = np.array([
            [*pmin],
            [pmax[0], pmin[1], pmin[2]],
            [*pmax],
            [pmin[0], pmax[1], pmin[2]],
            [pmin[0], pmin[1], pmax[2]],
            [pmax[0], pmin[1], pmax[2]],
            [*pmax],
            [pmin[0], pmax[1], pmax[2]],
        ])
        tris = np.array([
            [0,1,2],[0,2,3],[4,5,6],[4,6,7],
            [0,1,5],[0,5,4],[1,2,6],[1,6,5],
            [2,3,7],[2,7,6],[3,0,4],[3,4,7]
        ])
        self.fig.add_trace(go.Mesh3d(
            x=pts[:,0], y=pts[:,1], z=pts[:,2],
            i=tris[:,0], j=tris[:,1], k=tris[:,2],
            name=name, opacity=opacity, showlegend=False,
            hovertemplate=name
        ))

    def _update_plot(self):
        self.fig.data = []
        if self.main_region and self.toggle_show.value:
            self._plot_region(self.main_region, 'domain', 0.2)
        if not self.main_region:
            return
        for nm, rg in self._subregions.items():
            self._plot_region(rg, nm, 0.6)
        pmin, pmax = self.main_region.pmin, self.main_region.pmax
        dx, dy, dz = (pmax[0] - pmin[0], pmax[1] - pmin[1], pmax[2] - pmin[2])
        sc = self.fig.layout.scene
        sc.aspectratio = dict(x=dx, y=dy, z=dz)
        sc.xaxis.range = [pmin[0], pmax[0]]
        sc.yaxis.range = [pmin[1], pmax[1]]
        sc.zaxis.range = [pmin[2], pmax[2]]

    def _update_outliner(self):
        if not self.main_region:
            self.outliner_box.value = '<i>No domain set.</i>'
            return
        html = '<ul><li>main_region'
        for name in self._subregions:
            html += f"<ul><li>{name}</li></ul>"
        html += '</li></ul>'
        self.outliner_box.value = html

    def _refresh(self):
        bases = ['main'] + list(self._subregions.keys())
        # Update dropdowns in feature_modelling if referenced
        try:
            self._dd_div.options = bases
            self._dd_app.options = bases
            self._dd_rem.options = list(self._subregions.keys())
        except AttributeError:
            pass
        # Reset selector to last added or first
        if self.last_added in bases:
            self.model_selector.value = self.last_added
        else:
            self.model_selector.value = bases[0]

    def _on_workspace(self, change):
        idx = 0 if change['new'] == 'Modelling' else 1
        self.properties_pane.selected_index = idx

    # Callbacks
    def on_set_domain(self, _):
        try:
            pmin = self._convert(tuple(map(float, self._t_pmin.value.split(','))))
            pmax = self._convert(tuple(map(float, self._t_pmax.value.split(','))))
        except Exception:
            return
        self.main_region = df.Region(p1=pmin, p2=pmax, dims=self.dims, units=self.units)
        self._subregions.clear()
        self.last_added = None
        self._update_plot()
        self._update_outliner()
        self._refresh()

    def on_place(self, _):
        name = self._t_name.value.strip()
        try:
            pmin = self._convert(tuple(map(float, self._t_ppmin.value.split(','))))
            pmax = self._convert(tuple(map(float, self._t_ppmax.value.split(','))))
        except Exception:
            return
        if name and name not in self._subregions:
            self._subregions[name] = df.Region(p1=pmin, p2=pmax, dims=self.dims, units=self.units)
            self.last_added = name
            self._update_plot()
            self._update_outliner()
            self._refresh()

    def on_divide(self, _):
        base = self._dd_div.value
        name = self._t_divn.value.strip()
        sf = self._f_divsf.value
        if name and name not in self._subregions:
            parent = self.main_region if base == 'main' else self._subregions[base]
            newr = scaling_function(parent, sf, self.cellsize, 'max')
            self._subregions[name] = newr
            if base != 'main':
                del self._subregions[base]
            self.last_added = name
            self._update_plot()
            self._update_outliner()
            self._refresh()

    def on_append(self, _):
        base = self._dd_app.value
        side = self._tb_side.value
        name = self._t_appn.value.strip()
        sf = self._f_appsf.value
        if name and name not in self._subregions:
            parent = self.main_region if base == 'main' else self._subregions[base]
            piece = scaling_function(parent, sf, self.cellsize, side)
            newr = piece if base == 'main' else df.Region(p1=piece.pmin, p2=piece.pmax, dims=self.dims, units=self.units)
            self._subregions[name] = newr
            self.last_added = name
            self._update_plot()
            self._update_outliner()
            self._refresh()

    def on_remove(self, _):
        base = self._dd_rem.value
        if base in self._subregions:
            del self._subregions[base]
            self.last_added = None
            self._update_plot()
            self._update_outliner()
            self._refresh()

    def on_instantiate(self, _):
        mesh = self.mesh
        if mesh:
            print(mesh)

# usage example:
# designer = RegionDesigner(cellsize=(2e-9,1e-9,12e-9), show_borders=True)

# designer = RegionDesigner(cellsize=(2e-9,1e-9,12e-9), show_borders=True)
