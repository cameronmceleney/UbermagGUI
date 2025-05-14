#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Project: UbermagGUI
Path:    src/viewports/3d/plotly_3dmesh.py

Feature:
    3D mesh plotting interface 'feature' via Plotly FigureWidget. This file contains all widgets/panels
    in addition to creating the feature.
    
Author:      Cameron Aidan McEleney < c.mceleney.1@research.gla.ac.uk >
Created:     13 May 2025
IDE:         PyCharm
Version:     0.1.0
"""

# Standard library imports
import numpy as np
import plotly.graph_objs as go

# Third-party imports

# Local application imports
from src.config.type_aliases import UNIT_FACTORS

__all__ = ["Mesh3DPlot"]


class Mesh3DPlot:
    def __init__(self,
                 camera_eye: tuple[float, float, float] = (-1.25, -1.25, 1.25),
                 zoom_factor: float = 1.5):
        self._zoom = zoom_factor
        self._default_eye = np.array(camera_eye, float)
        self.camera_eye = camera_eye

        # Create the empty FigureWidget, then send dummy patch to ensure that
        # front-end comms. between coded widget and Jupyter Notebook are established
        # Otherwise, will lead to no update being pushed to Notebook!
        self.fig = go.FigureWidget(data=[])
        self.fig.layout.autosize = False
        # Now it's safe to create/update our FigureWidget
        self._init_figure_widget()

        # store last plotted bounds for reset
        self._last_bounds = None

    def plot(self, main_region, subregions: dict, show_domain: bool = True):
        """Update Viewport figure by clearing and re‐plotting main domain + subregions."""
        self.fig.data = []
        if main_region is None:
            return

        user_unit = main_region.units[0]
        factor = UNIT_FACTORS.get(user_unit, 1.0)

        # 1) domain
        if show_domain:
            self._add_mesh(main_region, "domain", 0.2, factor)

        # 2) subregions
        for name, region in subregions.items():
            self._add_mesh(region, name, 0.6, factor)

        # compute bounds in display units to...
        pmin = np.array(main_region.pmin) / factor
        pmax = np.array(main_region.pmax) / factor
        self._last_bounds = (pmin, pmax)

        # ...update scene aspectratio and axes
        dx, dy, dz = pmax - pmin
        scene = self.fig.layout.scene
        scene.aspectratio = dict(x=dx, y=dy, z=dz)
        scene.xaxis.range = [pmin[0], pmax[0]]
        scene.yaxis.range = [pmin[1], pmax[1]]
        scene.zaxis.range = [pmin[2], pmax[2]]

        scene.xaxis.title.text = f"x ({user_unit})"
        scene.yaxis.title.text = f"y ({user_unit})"
        scene.zaxis.title.text = f"z ({user_unit})"

        # reset camera to encompass entire bounds
        self._fit_camera(pmin, pmax)

    def reset_camera(self):
        """Re‐position camera to last plotted bounds."""
        if self._last_bounds is not None:
            pmin, pmax = self._last_bounds
            self._fit_camera(pmin, pmax)

    def _add_mesh(self, region, name, opacity, factor):
        pmin, pmax = region.pmin, region.pmax

        # build the 8 distinct corners of the cuboid in SI and convert to display units
        pts = np.array([
            [pmin[0], pmin[1], pmin[2]],
            [pmax[0], pmin[1], pmin[2]],
            [pmax[0], pmax[1], pmin[2]],
            [pmin[0], pmax[1], pmin[2]],
            [pmin[0], pmin[1], pmax[2]],
            [pmax[0], pmin[1], pmax[2]],
            [pmax[0], pmax[1], pmax[2]],
            [pmin[0], pmax[1], pmax[2]],
        ]) / factor

        tris = np.array([
            [0,1,2], [0,2,3], [4,5,6], [4,6,7],
            [0,1,5], [0,5,4], [1,2,6], [1,6,5],
            [2,3,7], [2,7,6], [3,0,4], [3,4,7]
        ])

        self.fig.add_trace(go.Mesh3d(
            x=pts[:,0], y=pts[:,1], z=pts[:,2],
            i=tris[:,0], j=tris[:,1], k=tris[:,2],
            name=name, opacity=opacity,
            showlegend=False, hovertemplate=name
        ))

    def _fit_camera(self, pmin: np.ndarray, pmax: np.ndarray):
        """
        Position the camera so the bounding sphere of [pmin,pmax] just fills
        the view, looking always at the true center.
        """

        center = (pmin + pmax) * 0.5  # center of the box
        v = self._default_eye - center  # vector from center → default eye
        v_norm = v / np.linalg.norm(v)

        half = (pmax - pmin) * 0.5  # radius of bounding sphere
        r = np.linalg.norm(half)

        fov = np.deg2rad(60)  # assume a 60° vertical field-of-view (fov) → half‐angle is 30°
        dist = (r / np.sin(fov/2)) * self._zoom

        eye = center + v_norm * dist

        # update Plotly camera; leave center at default (0,0,0) so it looks at data center
        self.fig.layout.scene.camera = dict(
            eye=dict(x=eye[0], y=eye[1], z=eye[2]),
            center=dict(x=0, y=0, z=0),
            up=dict(x=0, y=0, z=1),
        )

    def _init_figure_widget(self):
        # initial (will be overridden on first plot)
        cam = dict(eye=dict(x=self.camera_eye[0], y=self.camera_eye[1], z=self.camera_eye[2]))

        self.fig.update_layout(
            autosize=False,
            minreducedwidth=200,
            minreducedheight=200,
            margin=dict(l=30, r=30, t=30, b=30),  # Plotly (default) has massive margins; suggest imposing <= 30 px
            scene=dict(
                #domain=dict(x=[0, 1], y=[0, 1]),  # Use full area
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
