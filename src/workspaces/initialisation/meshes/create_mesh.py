#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Project: Ubermag
Path:    include/Uberwidgets/region_designer_interface/initialisation/fields/create_mesh.py

Description:

    MeshPanel: define your df.Mesh for the micromagnetic System.

    The user selects a region (default `main_region`), boundary conditions
    for each axis, and clicks "Build Mesh". On success, a Mesh object
    is created and passed to ControlsPanel via the registered callback.
    
Author:      Cameron Aidan McEleney < c.mceleney.1@research.gla.ac.uk >
Created:     04 May 2025
IDE:         PyCharm
Version:     0.1.0
"""

# Standard library imports
import ipywidgets as widgets
import logging
logger = logging.getLogger(__name__)

# Third-party imports
import discretisedfield as df

# Local application imports

__all__ = ["CreateMesh"]


class CreateMesh:
    def __init__(self):
        # callback to ControlsPanel: receives a Mesh instance
        self._mesh_cb = None
        self._plot_cb = None
        self._controls = None

        # widgets
        self.dd_base_region = None
        self.dd_bc_type = None
        self.ckk_bc_x = None
        self.ckk_bc_y = None
        self.ckk_bc_z = None
        self.btn_build_mesh = None

    def set_state_callback(self, cb):
        """Register ControlsPanel.set_mesh (or similar)."""
        self._mesh_cb = cb

    def build(self, controls_panel) -> widgets.VBox:
        """Build and return the UI for mesh creation."""
        self._controls = controls_panel

        panel = widgets.VBox(
            layout=widgets.Layout(
                width='auto',
                height='auto',
                overflow="auto",
                padding="4px"
            ),
        )
        children = []

        # 1) Explanation
        html_explainer = widgets.HTML(
            "<b>Generate mesh.</b>"
        )
        children.append(html_explainer)

        # Introductory text to the panel
        html_intro = widgets.HTML(
            value="Discretise a base region using a regular finite-difference method "
                  "to obtain a mesh. ",
            layout=widgets.Layout(
                width='auto',
            )
        )
        children.append(html_intro)

        # 1) Region selector
        html_base_region = widgets.HTML(
            value="Base region for mesh",
        )

        # 'Domain' region always called 'main'
        if self._controls.main_region is None:
            options_base_region = []
        else:
            options_base_region = ['main'] + list(self._controls.subregions.keys())
        self.dd_base_region = widgets.Dropdown(
            options=options_base_region,
            layout=widgets.Layout(width="40%")
        )

        hbox_base_region = widgets.HBox(
            children=[html_base_region, self.dd_base_region],
            layout=widgets.Layout(
                width='auto',
                height='auto',
                align_items='center',
                align_content='center',
                justify_content='flex-end',
            )
        )
        children.append(hbox_base_region)

        # 2) Stack that rotates through BC options
        self._build_boundary_conditions(children)

        # 3) Build mesh button
        self.btn_build_mesh = widgets.Button(
            description="Build Mesh",
            button_style='primary',
            layout=widgets.Layout(width="auto")
        )
        self.btn_build_mesh.on_click(self._on_create_mesh)

        btn_box = widgets.HBox(
            [self.btn_build_mesh],
            layout=widgets.Layout(justify_content="center", padding='4px'))
        children.append(btn_box)

        panel.children = tuple(children)
        return panel

    def refresh(self, bases):
        """
        Refresh region dropdown when subregions change.
        `bases` must be ['main', sub1, sub2, …].
        """

        if self._controls.main_region is None:
            self.dd_base_region.options = []
            self.dd_base_region.value = None
            self.btn_build_mesh.disabled = True
            return

        self.dd_base_region.options = bases
        if self.dd_base_region.value not in bases:
            self.dd_base_region.value = bases[0]
        self.btn_build_mesh.disabled = False
        self.btn_build_mesh.button_style = ''

    def _on_create_mesh(self, _):
        """Instantiate df.Mesh from UI and invoke the callback."""
        key = self.dd_base_region.value

        # select base region
        parent = (self._controls.main_region if key=='main' else self._controls.subregions.get(key))
        if parent is None:
            self.btn_build_mesh.button_style = 'danger'
            return

        try:
            mesh = df.Mesh(
                region=parent,
                cell=self._controls.cellsize,
                subregions={},
                bc=self._on_dropdown_bc()
            )
        except Exception as e:
            logger.error("Mesh creation failed: %s", e, exc_info=True)
            self.btn_build_mesh.button_style = "danger"
            return

        self.btn_build_mesh.button_style = 'success'

        # Notify ControlsPanel of new mesh
        if self._mesh_cb:
            self._mesh_cb(mesh)

        self.refresh(['main'] + list(self._controls.subregions.keys()))

    def _build_boundary_conditions(self, children):
        """
        Ubermag is updating which boundary conditions are available.

        This function is a placeholder for the future.
        """
        # 1) Explain to user how BC are set
        html_explainer = widgets.HTMLMath(
            value=(
                f"Boundary conditions should be specified. "
                f"The default setting in Ubermag is Open. "
            ),
            layout=widgets.Layout(
                overflow_y="visible",
                width="auto"
            )
        )
        children.append(html_explainer)

        # 2) Create DropDown to handle input of BC type
        bc_opts = [
            ("Open", "open"),
            ("Periodic", "periodic"),
            ("Neumann", "neumann"),
            ("Dirichlet", "dirichlet"),
        ]
        max_label_length = max(len(label) for label, _ in bc_opts)
        dd_width = f"{max_label_length * 1.5 + 2}ch"
        self.dd_bc_type = widgets.Dropdown(
            options=bc_opts,
            value="open",
            layout=widgets.Layout(width=dd_width)
        )

        # 3) Create widgets for each BC type
        # 3.1) Open BC - no additional options needed so add a spacer
        html_placeholder = widgets.HTML(
            value="<b>None</b>",
            layout=widgets.Layout(width="auto")
        )
        hbox_placeholder = widgets.HBox(
            children=[html_placeholder],
            layout=widgets.Layout(
                width="auto",
                height="auto",
                align_items='center',
                gap="4px")
        )

        # 3.2) Periodic BC - one checkbox for each cartesian axis
        self.ckk_bc_x = widgets.Checkbox(
            description='x',
            value=False,
            style={'description_width': '2rem'},
            layout=widgets.Layout(width="auto")
        )

        self.ckk_bc_y = widgets.Checkbox(
            description='y',
            value=False,
            style={'description_width': '2rem'},
            layout=widgets.Layout(width="auto")
        )

        self.ckk_bc_z = widgets.Checkbox(
            description='z',
            value=False,
            style={'description_width': '2rem'},
            layout=widgets.Layout(width="auto")
        )

        hbox_periodic_bc = widgets.HBox(
            children=[self.ckk_bc_x, self.ckk_bc_y, self.ckk_bc_z],
            layout=widgets.Layout(
                width='100%',
                align_items='center',
                #justify_content='center',
                gap="4px")
        )
        
        # 3.3) Neumann BC - no additional options needed so add a spacer
        hbox_neumann = widgets.HBox([widgets.HTML(value="<b>None</b>")],
                                    layout=widgets.Layout(align_items='center', gap='4px'))
        # 3.4) Dirichlet BC - one text box for each cartesian axis
        hbox_dirichlet = widgets.HBox([widgets.HTML(value="<b>None</b>")],
                                      layout=widgets.Layout(align_items='center', gap='4px'))

        # Create stack of widgets and link to DropDown
        stack_bc = widgets.Stack(
            children=[hbox_placeholder, hbox_periodic_bc, hbox_neumann, hbox_dirichlet],
            selected_index=0,
            layout=widgets.Layout(width="auto")
        )
        widgets.jslink((self.dd_bc_type, 'index'), (stack_bc, 'selected_index'))

        # --------
        # Create box to hold the DropDown and the stack
        hbox_dropdown_plus_stack = widgets.VBox(
            children=[self.dd_bc_type, stack_bc],
            layout=widgets.Layout(
                width="auto",
                height="auto",
                align_items='center',
                gap="4px")
        )

        children.append(hbox_dropdown_plus_stack)

    def _on_dropdown_bc(self):
        """Return string for BC type as required by Ubermag"""
        if self.dd_bc_type.value == 'open': return ''

        if self.dd_bc_type.value == 'periodic':
            bc = ''

            if self.ckk_bc_x.value:
                bc += 'x'
            if self.ckk_bc_y.value:
                bc += 'y'
            if self.ckk_bc_z.value:
                bc += 'z'

            if len(bc) == 0:
                self.dd_bc_type.value = 'open'

            return bc

        if self.dd_bc_type.value == 'dirichlet': return 'dirichlet'

        if self.dd_bc_type.value == 'neumann': return 'neumann'

        raise NotImplementedError


