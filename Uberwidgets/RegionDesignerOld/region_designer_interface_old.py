#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Project: Ubermag
Path:    include/Uberwidgets/region_designer_interface/region_designer_interface_old.py

Description:
    GUI for interactively defining a main domain region, placing subregions,
    dividing existing subregions, appending slices, removing regions,
    logging events, listing regions, managing presets, and customizing plot options.

Author:      Cameron Aidan McEleney <c.mceleney.1@research.gla.ac.uk>
Created:     28 Apr 2025
Version:     0.4.0
"""

from IPython.display import display
import ipywidgets as widgets
import numpy as np
import plotly.graph_objs as go
from plotly.graph_objs import FigureWidget
import discretisedfield as df


def scaling_function(input_region: df.Region,
                     scale_factor: float,
                     cellsize: tuple,
                     side: str = 'max') -> df.Region:
    """
    Slice off a 1-cell slab on the specified x-face ('max' or 'min'),
    then scale that slab along x by scale_factor using Ubermag's .scale().
    """
    dims = getattr(input_region, 'dims', None)
    units = getattr(input_region, 'units', None)
    if side == 'max':
        p1 = (input_region.pmax[0], input_region.pmin[1], input_region.pmin[2])
        p2 = (input_region.pmax[0] + cellsize[0], input_region.pmax[1], input_region.pmax[2])
    else:
        p1 = (input_region.pmin[0] - cellsize[0], input_region.pmin[1], input_region.pmin[2])
        p2 = (input_region.pmin[0], input_region.pmax[1], input_region.pmax[2])
    slab = df.Region(p1=p1, p2=p2, dims=dims, units=units)
    scaled = slab.scale(factor=(scale_factor, 1, 1), reference_point=slab.pmin, inplace=False)
    new_pmin = tuple(round(x, 9) for x in scaled.pmin)
    new_pmax = tuple(round(x, 9) for x in scaled.pmax)
    return df.Region(p1=new_pmin, p2=new_pmax, dims=dims, units=units)


class RegionDesigner:
    def __init__(self,
                 cellsize=(2e-9, 1e-9, 12e-9),
                 dims=('x', 'y', 'z'),
                 units=('m', 'm', 'm')):
        self.cellsize = cellsize
        self.dims = dims
        self.units = units
        self.main_region = None
        self._subregions = {}
        self.last_added = None
        # example presets
        self.presets = {
            'Example': {
                'domain': ((0.0, 0.0, 0.0), (1e-8, 5e-9, 2e-8)),
                'subregions': {'preset1': ((0.0, 0.0, 0.0), (5e-9, 5e-9, 2e-8))}
            }
        }
        # build UI
        self._make_widgets()
        self._make_figure()
        # observe show domain toggle
        self.toggle_main.observe(lambda _: self._update_plot(), names='value')
        # layout
        self.header = widgets.HTML('<h2>Region Designer</h2>')
        # left: modelling and presets
        self.left_tabs = widgets.Tab(children=[self.accordion, self.presets_box])
        self.left_tabs.set_title(0, 'Modelling')
        self.left_tabs.set_title(1, 'Presets')
        # right: event log, regions list, options
        self.right_tabs = widgets.Tab(children=[self.event_log, self.regions_list, self.options_box])
        self.right_tabs.set_title(0, 'Event Log')
        self.right_tabs.set_title(1, 'List of regions')
        self.right_tabs.set_title(2, 'Options')
        layout = widgets.AppLayout(
            header=self.header,
            left_sidebar=self.left_tabs,
            center=self.center,
            right_sidebar=self.right_tabs,
            footer=self.bottom_controls,
            pane_widths=['25%', '60%', '15%']
        )
        display(layout)
        self._log_event('Interface initialized.')

    @property
    def subregions(self):
        return self._subregions

    @property
    def mesh(self):
        if self.main_region is None:
            return None
        return df.Mesh(region=self.main_region,
                       cell=self.cellsize,
                       subregions=self._subregions)

    def _make_widgets(self):
        # Domain
        self.pmin_text = widgets.Text(description='pmin (x,y,z):')
        self.pmax_text = widgets.Text(description='pmax (x,y,z):')
        self.btn_domain = widgets.Button(description='Initialize Domain')
        self.btn_domain.on_click(self.on_set_domain)
        domain_box = widgets.VBox([self.pmin_text, self.pmax_text, self.btn_domain])
        # Place
        self.place_name = widgets.Text(description='Name:')
        self.place_pmin = widgets.Text(description='pmin (x,y,z):')
        self.place_pmax = widgets.Text(description='pmax (x,y,z):')
        self.btn_place = widgets.Button(description='Place Region')
        self.btn_place.on_click(self.on_place)
        place_box = widgets.VBox([self.place_name, self.place_pmin, self.place_pmax, self.btn_place])
        # Divide
        self.dd_divide_base = widgets.Dropdown(options=[], description='Base:')
        self.chk_x = widgets.Checkbox(True, description='X-axis')
        self.chk_y = widgets.Checkbox(False, description='Y-axis')
        self.chk_z = widgets.Checkbox(False, description='Z-axis')
        self.div_name = widgets.Text(description='Name:')
        self.div_scale = widgets.FloatText(1.0, description='Scale:')
        self.btn_divide = widgets.Button(description='Divide')
        self.btn_divide.on_click(self.on_divide)
        divide_box = widgets.VBox([self.dd_divide_base,
                                  widgets.HBox([self.chk_x, self.chk_y, self.chk_z]),
                                  self.div_name, self.div_scale, self.btn_divide])
        # Append
        self.dd_append_base = widgets.Dropdown(options=[], description='Base:')
        self.append_side = widgets.ToggleButtons(options=[('From Min','min'),('From Max','max')], description='Side:')
        self.extrude_label = widgets.HTML('<b>Extrude along:</b>')
        self.ex_x = widgets.Checkbox(True, description='x')
        self.ex_y = widgets.Checkbox(False, description='y')
        self.ex_z = widgets.Checkbox(False, description='z')
        extrude_box = widgets.HBox([self.ex_x, self.ex_y, self.ex_z])
        self.app_name = widgets.Text(description='Name:')
        self.app_scale = widgets.FloatText(1.0, description='Scale:')
        self.btn_append = widgets.Button(description='Append')
        self.btn_append.on_click(self.on_append)
        append_box = widgets.VBox([self.dd_append_base, self.append_side,
                                   self.extrude_label, extrude_box,
                                   self.app_name, self.app_scale, self.btn_append])
        # Remove
        self.dd_remove = widgets.Dropdown(options=[], description='Region:')
        self.btn_remove = widgets.Button(description='Delete Region')
        self.btn_remove.on_click(self.on_remove)
        remove_box = widgets.VBox([self.dd_remove, self.btn_remove])
        # Accordion
        self.accordion = widgets.Accordion([domain_box, place_box, divide_box, append_box, remove_box])
        for i, title in enumerate(['Domain','Place','Divide','Append','Remove']):
            self.accordion.set_title(i, title)
        # Presets
        self.preset_dd = widgets.Dropdown(options=list(self.presets.keys()), description='Preset:')
        self.btn_load = widgets.Button(description='Load')
        self.btn_load.on_click(self.on_load)
        self.btn_save = widgets.Button(description='Save')
        self.btn_save.on_click(self.on_save)
        self.presets_box = widgets.VBox([self.preset_dd, widgets.HBox([self.btn_load, self.btn_save])])
        # Event log and Regions list
        self.event_log = widgets.Textarea(value='', disabled=True,
                                         layout=widgets.Layout(width='100%', height='200px'))
        self.regions_list = widgets.Textarea(value='', disabled=True,
                                            layout=widgets.Layout(width='100%', height='200px'))
        # Options
        self.toggle_main = widgets.Checkbox(value=True, description='Show Domain')
        self.units_dd = widgets.Dropdown(options=['nm','um','m'], value='nm', description='Units:')
        self.options_box = widgets.VBox([self.toggle_main, self.units_dd])
        # Instantiate button
        self.btn_instant = widgets.Button(description='Instantiate')
        self.btn_instant.on_click(self.on_instantiate)
        # Bottom controls
        self.bottom_controls = widgets.HBox([self.btn_instant])

    def _make_figure(self):
        initial_camera = dict(eye=dict(x=-1.25, y=-1.25, z=1.25))
        self.fig = FigureWidget(layout=go.Layout(
            scene=dict(aspectmode='manual', camera=initial_camera),
            uirevision='camera'
        ))
        self.center = widgets.Box([self.fig])
        self._update_plot()

    def _plot_region(self, region: df.Region, name: str, opacity: float):
        pmin, pmax = region.pmin, region.pmax
        pts = np.array([[pmin[0],pmin[1],pmin[2]], [pmax[0],pmin[1],pmin[2]],
                        [pmax[0],pmax[1],pmin[2]], [pmin[0],pmax[1],pmin[2]],
                        [pmin[0],pmin[1],pmax[2]], [pmax[0],pmin[1],pmax[2]],
                        [pmax[0],pmax[1],pmax[2]], [pmin[0],pmax[1],pmax[2]]])
        tris = np.array([[0,1,2],[0,2,3],[4,5,6],[4,6,7],
                         [0,1,5],[0,5,4],[1,2,6],[1,6,5],
                         [2,3,7],[2,7,6],[3,0,4],[3,4,7]])
        cen = pts.mean(axis=0)
        mesh = go.Mesh3d(x=pts[:,0], y=pts[:,1], z=pts[:,2],
                         i=tris[:,0], j=tris[:,1], k=tris[:,2],
                         name=name, opacity=opacity, showlegend=False,
                         hoverinfo='none', hovertext=name, hovertemplate=name)
        self.fig.add_trace(mesh)
        marker = go.Scatter3d(x=[cen[0]], y=[cen[1]], z=[cen[2]],
                              mode='markers', marker=dict(size=8, color='rgba(0,0,0,0)'),
                              showlegend=False, hoverinfo='none')
        self.fig.add_trace(marker)
        rid = 'main' if name=='domain' else name
        marker.on_click(lambda trace, pts, state: [
            setattr(self.dd_divide_base, 'value', rid),
            setattr(self.dd_append_base, 'value', rid)
        ])

    def _update_plot(self):
        self.fig.data = []
        if self.main_region and self.toggle_main.value:
            self._plot_region(self.main_region, 'domain', 0.2)
        if self.main_region:
            for nm, reg in self._subregions.items():
                self._plot_region(reg, nm, 0.6)
            pmin, pmax = self.main_region.pmin, self.main_region.pmax
            dx, dy, dz = pmax[0]-pmin[0], pmax[1]-pmin[1], pmax[2]-pmin[2]
            scene = self.fig.layout.scene
            scene.aspectratio = dict(x=dx, y=dy, z=dz)
            scene.xaxis.range = [pmin[0], pmax[0]]
            scene.yaxis.range = [pmin[1], pmax[1]]
            scene.zaxis.range = [pmin[2], pmax[2]]

    def _refresh_dropdowns(self):
        bases = ['main'] + list(self._subregions.keys())
        self.dd_divide_base.options = bases
        self.dd_append_base.options = bases
        self.dd_remove.options = list(self._subregions.keys())
        if self.last_added in bases:
            self.dd_divide_base.value = self.last_added
            self.dd_append_base.value = self.last_added
        else:
            self.dd_divide_base.value = 'main'
            self.dd_append_base.value = 'main'

    def _log_event(self, msg: str):
        self.event_log.value += f'• {msg}\n\n'

    def _update_regions_list(self):
        txt = ''
        for name, reg in self._subregions.items():
            txt += f"{name}: {reg}\n"
        self.regions_list.value = txt

    # --- Callbacks ---
    def on_set_domain(self, _):
        self.event_log.value = ''
        try:
            pmin = tuple(map(float, self.pmin_text.value.split(',')))
            pmax = tuple(map(float, self.pmax_text.value.split(',')))
        except:
            self._log_event('Error: malformed domain pmin/pmax.')
            return
        self.main_region = df.Region(p1=pmin, p2=pmax, dims=self.dims, units=self.units)
        self._subregions.clear()
        self.last_added = None
        self._refresh_dropdowns()
        self._update_plot()
        self._log_event('Domain initialized.')
        self._update_regions_list()

    def on_place(self, _):
        name = self.place_name.value.strip()
        if not name or name in self._subregions:
            self._log_event(f"Error placing '{name}'.")
            return
        try:
            pmin = tuple(map(float, self.place_pmin.value.split(',')))
            pmax = tuple(map(float, self.place_pmax.value.split(',')))
        except:
            self._log_event('Error: malformed place pmin/pmax.')
            return
        self._subregions[name] = df.Region(p1=pmin, p2=pmax, dims=self.dims, units=self.units)
        self.last_added = name
        self._refresh_dropdowns()
        self._update_plot()
        self._log_event(f"Placed '{name}'.")
        self._update_regions_list()

    def on_divide(self, _):
        base = self.dd_divide_base.value
        name = self.div_name.value.strip()
        sf = self.div_scale.value
        if not name or name in self._subregions:
            self._log_event(f"Error dividing into '{name}'.")
            return
        parent = self.main_region if base=='main' else self._subregions[base]
        new_r = scaling_function(parent, sf, self.cellsize, side='max')
        self._subregions[name] = new_r
        if base!='main':
            self._subregions.pop(base)
        self.last_added = name
        self._refresh_dropdowns()
        self._update_plot()
        self._log_event(f"Divided '{base}' → '{name}'.")
        self._update_regions_list()

    def on_append(self, _):
        base = self.dd_append_base.value
        side = self.append_side.value
        name = self.app_name.value.strip()
        sf = self.app_scale.value
        if not name or name in self._subregions:
            self._log_event(f"Error appending '{name}'.")
            return
        parent = self.main_region if base=='main' else self._subregions[base]
        piece = scaling_function(parent, sf, self.cellsize, side)
        if base=='main':
            new_r = piece
        else:
            new_r = df.Region(p1=piece.pmin, p2=piece.pmax, dims=self.dims, units=self.units)
        self._subregions[name] = new_r
        self.last_added = name
        self._refresh_dropdowns()
        self._update_plot()
        self._log_event(f"Appended '{name}' at {side}.")
        self._update_regions_list()

    def on_remove(self, _):
        name = self.dd_remove.value
        if name in self._subregions:
            self._subregions.pop(name)
            self._refresh_dropdowns()
            self._update_plot()
            self._log_event(f"Removed '{name}'.")
            self._update_regions_list()

    def on_load(self, _):
        preset = self.preset_dd.value
        cfg = self.presets.get(preset)
        if not cfg:
            self._log_event(f"Preset '{preset}' not found.")
            return
        # load domain
        domain = cfg['domain']
        self.main_region = df.Region(p1=domain[0], p2=domain[1], dims=self.dims, units=self.units)
        # load subregions
        self._subregions.clear()
        for nm, bounds in cfg['subregions'].items():
            self._subregions[nm] = df.Region(p1=bounds[0], p2=bounds[1], dims=self.dims, units=self.units)
        self.last_added = next(iter(cfg['subregions']))
        self._refresh_dropdowns()
        self._update_plot()
        self._log_event(f"Loaded preset '{preset}'.")
        self._update_regions_list()

    def on_save(self, _):
        self._log_event('Save functionality placeholder.')

    def on_instantiate(self, _):
        if self.main_region is None:
            self._log_event('Error: domain not initialized.')
            return
        mesh = self.mesh
        self._log_event('Mesh instantiated.')
        print(mesh)

# Usage:
# from Uberwidgets.region_designer_interface.region_designer_interface import RegionDesigner
# designer = RegionDesigner(cellsize=(2e-9,1e-9,12e-9))
