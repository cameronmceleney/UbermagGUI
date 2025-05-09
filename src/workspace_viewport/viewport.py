#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Defines the 3D plot area and toolbar using Plotly's FigureWidget.
"""

import numpy as np
import ipywidgets as widgets
from ipywidgets import Layout, GridspecLayout
from config.type_aliases import UNIT_FACTORS
import plotly.graph_objects as go

__all__ = ["ViewportArea"]


class ViewportArea:
    def __init__(self, camera_eye=(-1.25, -1.25, 1.25), zoom_factor=1.5):

        self._zoom = zoom_factor
        self._default_eye = np.array(camera_eye, float)
        self.camera_eye = camera_eye

        # Send a dummy patch to self.fig to ensure that front-end communications are established
        self.fig = go.FigureWidget(data=[])
        self.fig.layout.autosize = False

        # TODO. Move custom plot-visualisation functionalities (change to 2D/3D plot etc) here
        self.toolbar = widgets.HBox(
            [widgets.Button(description="Reset Camera", layout=Layout(width="auto"))],
            layout=Layout(justify_content="flex-start"),
        )

    def build(self):
        grid = GridspecLayout(
            n_rows=2, n_columns=1,
            layout=widgets.Layout(
                width="100%",
                height="100%",
                gap='4px',
            )
        )
        grid._grid_template_rows = "90% 10%"

        # Place in build(), not __init__, to further protect against update failures
        self._init_fig_widget()

        # wrap fig in a Box so grid_area is applied correctly
        fig_container = widgets.Box(
            [self.fig],
            #layout=Layout(
                #display='flex',
                #flex="1 1 auto",
                #width="100%",
                #height='100%',
                #overflow="hidden"  # Prevents weird rendering of plot labels if fig-space is too small
            #)
        )

        grid[0, 0] = fig_container
        grid[1, 0] = self.toolbar
        return grid

    def plot_regions(self, main_region, subregions, show_domain=True):
        """Update Viewport figure"""
        # TODO. Change method inputs to be Ubermag properties like df.Mesh
        # clear existing traces
        self.fig.data = []

        if not main_region:
            return

        user_unit = main_region.units[0]
        factor = UNIT_FACTORS.get(user_unit, 1.0)

        # plot main domain
        if show_domain:
            self._add_mesh(main_region, "domain", 0.2, factor)
        # plot subregions
        for nm, rg in subregions.items():
            self._add_mesh(rg, nm, 0.6, factor)

        # now adjust aspectratio & ranges in display units
        pmin = np.array(main_region.pmin) / factor
        pmax = np.array(main_region.pmax) / factor
        dx, dy, dz = pmax - pmin

        scene = self.fig.layout.scene
        scene.aspectratio = dict(x=dx, y=dy, z=dz)
        scene.xaxis.range = [pmin[0], pmax[0]]
        scene.yaxis.range = [pmin[1], pmax[1]]
        scene.zaxis.range = [pmin[2], pmax[2]]

        # label axes with user units
        scene.xaxis.title.text = f"x ({user_unit})"
        scene.yaxis.title.text = f"y ({user_unit})"
        scene.zaxis.title.text = f"z ({user_unit})"

        self._fit_camera(pmin, pmax)

    def _fit_camera(self, pmin: np.ndarray, pmax: np.ndarray):
        """
        Position the camera so the bounding sphere of [pmin,pmax] just fills
        the view, looking always at the true center.
        """
        # center of the box
        center = (pmin + pmax) * 0.5
        # vector from center → default eye
        v = self._default_eye - center
        v_norm = v / np.linalg.norm(v)

        # radius of bounding sphere
        half = (pmax - pmin) * 0.5
        r = np.linalg.norm(half)

        # assume a 60° vertical fov → half‐angle is 30°
        fov = np.deg2rad(60)
        dist = (r / np.sin(fov / 2)) * self._zoom

        new_eye = center + v_norm * dist

        # update Plotly camera; leave center at default (0,0,0) so it looks at data center
        self.fig.layout.scene.camera = dict(
            eye=dict(x=new_eye[0], y=new_eye[1], z=new_eye[2]),
            center=dict(x=0, y=0, z=0),
            up=dict(x=0, y=0, z=1),
        )

    def _add_mesh(self, region, name, opacity, factor):
        pmin, pmax = region.pmin, region.pmax

        # build the 8 distinct corners of the cuboid in SI
        display_pts = np.array([
            [pmin[0], pmin[1], pmin[2]],
            [pmax[0], pmin[1], pmin[2]],
            [pmax[0], pmax[1], pmin[2]],
            [pmin[0], pmax[1], pmin[2]],
            [pmin[0], pmin[1], pmax[2]],
            [pmax[0], pmin[1], pmax[2]],
            [pmax[0], pmax[1], pmax[2]],
            [pmin[0], pmax[1], pmax[2]],
        ])

        # convert to display units
        display_pts /= factor

        tris = np.array([
            [0,1,2], [0,2,3], [4,5,6], [4,6,7],
            [0,1,5], [0,5,4], [1,2,6], [1,6,5],
            [2,3,7], [2,7,6], [3,0,4], [3,4,7]
        ])

        self.fig.add_trace(go.Mesh3d(
            x=display_pts[:,0], y=display_pts[:,1], z=display_pts[:,2],
            i=tris[:,0], j=tris[:,1], k=tris[:,2],
            visible=True,
            name=name, opacity=opacity, showlegend=False,
            hovertemplate=name
            )
        )

    def _init_fig_widget(self):

        # initial (will be overridden on first plot)
        cam = dict(eye=dict(x=self.camera_eye[0], y=self.camera_eye[1], z=self.camera_eye[2]))

        self.fig.update_layout(
            autosize=True,
            minreducedwidth=400,
            minreducedheight=400,
            margin=dict(l=0, r=0, t=0, b=0),  # Attempt to minimise massive default margins
            scene=dict(
                # domain=dict(x=[0, 1], y=[0, 1]),  # Use full area
                aspectmode="auto",
                camera=cam
            ),
            uirevision="camera",
            modebar=dict(
                orientation='v',
                remove=[#'resetCameraDefault3d',
                        'resetCameraLastSave3d'],
            )
        )
