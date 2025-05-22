#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Project: UbermagGUI
Path:    src/workspaces/utils/feature_base.py

SingleFeatureController:
    Abstract base to build a toggle-selector + content region for a group of panels.

WorkspaceFeatureController:
    Text.
    
Author:      Cameron Aidan McEleney < c.mceleney.1@research.gla.ac.uk >
Created:     22 May 2025
IDE:         PyCharm
Version:     0.1.0
"""

# Standard library imports
from abc import ABC, abstractmethod
import ipywidgets as widgets
from typing import Any, Mapping

# Third-party imports

# Local application imports

__all__ = [
    "SingleFeatureController",
    "GroupFeatureController"
]


class SingleFeatureController(ABC):
    """
    Abstract base for a *feature group* in the workspace area,
    e.g. the “Geometry” feature or the “Mesh” feature under “System Init”.

    Responsibilities:
      • holds a mapping of panel-name → panel-instance
      • builds a two-column layout: left = ToggleButtons, right = panel content
      • routes `selector` clicks into `.build(...)` and optional `.refresh()`

    Subclasses *must* implement:

    Attributes
    ----------
    _panels : dict[str, Any]
        Will be filled by build_feature(...). Map a keyword (used by callbacks) to each panel in the feature.

    _selector : widgets.ToggleButtons | None
        Backing attribute for widget to enable toggling between *panels* within the *feature*.

    _panel_area : widgets.Box | None
        Backing attribute to combine selector + panels into single container for use in feature's tabs.
     """
    _panels: dict[str, Any]
    _selector: widgets.ToggleButtons | None
    _panel_area: widgets.Box | None

    def __init__(
            self,
            properties_controller: Any  # TODO. Get futures working for type hinting
    ):
        """
        Parameters
        ---------
        _sys_props : Any
            Live, shared properties for the entire interface.
        """
        self._sys_props: Any = properties_controller

        self._panels = {}
        self._selector = None
        self._panel_area = None

    # TODO. Create an @abstractclass for build()

    def build_feature(self, panel_map: dict) -> widgets.GridspecLayout:
        """
        Build a two-column layout for the feature: [ selector | content ]

        Parameters
        ----------
        panel_map:
            Mapping of panel-name (selector) to panel-instance (must support .build(self))
        """
        # Stash for children
        self._panels = panel_map

        # Create from properties
        selector = self.selector
        content = self.panel_area

        # Build feature
        feature_grid = widgets.GridspecLayout(
            n_rows=1, n_columns=2,
            layout=widgets.Layout(
                display='flex',
                min_height='0',
                gap='4px',
                overflow='hidden',
            )
        )

        # 1st column follows own Layout, and 2nd column fills remaining space
        feature_grid._grid_template_columns = f'{selector.style.button_width} 1fr'

        feature_grid[0, 0] = selector
        feature_grid[0, 1] = content

        self._render_panel(selector.value)

        return feature_grid

    @property
    def selector(self) -> widgets.ToggleButtons:
        """
        Construct the ToggleButtons used to change between panels of this feature, and setup the
        wiring required by `workspace_controller.py` and other higher-level controllers.
        """
        if self._selector is None:
            names = list(self._panels.keys())

            # Guaranteeing widths will be particularly helpful when displaying icons
            min_width = '10ch'  # str(min(max(len(n) for n in names), 8) + 2) + "ch"

            self._selector = widgets.ToggleButtons(
                options=names,
                tooltips=tuple(names),
                button_style='',  # greyed out
                style={
                    'button_width': min_width,
                    'align_content': 'center',
                    'justify_content': 'center'
                },
                layout=widgets.Layout(
                    display='flex',  # required for column-nowrap to take effect
                    flex_flow='column nowrap',
                    min_width=min_width, width=min_width,
                    overflow='hidden',
                ),
            )

            self._selector.observe(self._on_select, names='value')

            if names:
                self._selector.value = names[0]

        return self._selector

    @property
    def panel_area(self) -> widgets.Box:
        """
        Host the active panel's built UI.

        Lazily constructed when first accessed.
        """
        if self._panel_area is None:
            self._panel_area: widgets.Box = widgets.Box(
                layout=widgets.Layout(
                    display='flex',
                    flex='1 1 auto',
                    flex_flow='column nowrap',
                    width='100%', min_width='0',
                    min_height='0',
                    overflow_x="hidden",
                    overflow_y="auto"
                )
            )
        return self._panel_area

    def _on_select(self, change: dict) -> None:
        """Handles when ToggleButtons' value changes."""
        if change.get('name') == 'value':
            self._render_panel(change['new'])

    def _render_panel(self, panel_name: str) -> None:
        """Clear the active box, and display the chosen panel."""
        feature = self._panels.get(panel_name)
        panel_requested = feature.build(self._sys_props)

        if panel_requested is None:
            return

        # if this panel has a `.refresh()`, give it a chance to sync before we display
        if hasattr(feature, "refresh"):
            feature.refresh()

        self._panel_area.children = (panel_requested,)


class GroupFeatureController(ABC):
    """
    Abstract base for a top‐level workspace *feature* (e.g. “Initialisation”,
    “Equations”); also referred to as a workspace *feature-grouping*.

    Each subclass wires together one or more SingleFeatureController sub‐features (Geometry, Mesh, Energy, Dynamics, …)
    under a single container (often a Tab).

    Subclasses must implement:
        - `build(self) -> widgets.Widget`

    Return the container that hosts all their SingleFeatureController sub‐features.

    Attributes
    ----------
    features : dict[str, Any]
        Maps keyword used in callbacks to the controller for a feature
    """
    features: dict[str, Any] = {}

    @abstractmethod
    def build(self) -> widgets.Widget:
        """
        Build (or reuse) and return this feature’s root widget (often a Tab).

        Subclasses *must* call `self._make_tab(...)` if they want a standard Tab layout.
        """
        ...

    def _make_tab(
            self,
            features: Any,  # TODO. Provide typing for this kwarg
            *,
            layout: widgets.Layout | None = None
    ) -> widgets.Tab:
        """
         Helper to build a Tab from a dict of name→SingleFeatureController.
         Automatically builds each sub‐feature, wires them in, and sets titles.
         """
        # Defaults to None due to arg default
        layout = layout or widgets.Layout(
            display='flex',
            flex='1 1 0',
            width='100%',
            height='100%',
            overflow='hidden'
        )

        tab = widgets.Tab(children=[f.build() for f in features.values()],
                          layout=layout)

        for idx, title in enumerate(features):
            tab.set_title(idx, title)

        return tab
