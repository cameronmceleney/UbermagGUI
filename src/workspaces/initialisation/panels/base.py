#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Project: UbermagGUI
Path:    src/workspaces/initialisation/panels/base.py

Description:
    Short description of what this (base.py) does.
    
Author:      Cameron Aidan McEleney < c.mceleney.1@research.gla.ac.uk >
Created:     19 May 2025
IDE:         PyCharm
Version:     0.1.0
"""

# Standard library imports
from abc import ABC, abstractmethod
import ipywidgets as widgets
from typing import Any, Callable, List, Optional, Sequence

# Third-party imports

# Local application imports

__all__ = ["_PanelBase"]


class _PanelBase(ABC):
    """
    Abstract base for all workspace panels.

    Responsibilities:
      - store a `state_callback`
      - hold onto `context` (sys_props)
      - create a VBox container with a consistent layout
      - call out to `_compose` to fill its children
      - wire any default button callbacks
    """

    def __init__(self):
        # callback into the controller. Used to be called `state_cb` and `mesh_cb`
        self._ctrl_cb: Any = None
        # _CoreProperties. that is on build()
        self._sys_props: Any = None

        # layout parameters for every panel
        self._layout = widgets.Layout(
            width='100%',
            min_height='0', height=None,
            overflow_x='hidden',
            overflow_y='scroll',
            padding='4px',
        )

        # the single VBox that will house this panel
        self._panel_box: Optional[widgets.Box] = None

    def set_state_callback(self, cb: Any):
        """
        Register the callback used by this panel to report back
        (e.g. new region, new mesh, new field, etc).

        Concrete subclasses MUST implement this.
        """
        self._ctrl_cb = cb

    def build(self, context: Any) -> widgets.VBox:
        """
        Build (or reuse) the panel container, populate it, and return it.
        """
        self._sys_props = context
        if self._panel_box is None:
            # only create once
            self._panel_box = widgets.VBox(layout=self._layout)

        # let the concrete panel fill out its own children
        children: List[widgets.Widget] = []
        self._assemble_panel(children)

        # wire up any default button callbacks, if present
        # self._wire_callbacks()  # TODO. implement this abstractclass

        self._panel_box.children = tuple(children)  # Casting is essential
        return self._panel_box

    @abstractmethod
    def _assemble_panel(self, children: List[widgets.Widget]) -> None:
        """
        Append all the widgets that make up this panel to `children`.

        Called each time ``build(...)`` is run. Concrete subclasses MUST implement this.
        """

    @abstractmethod
    def refresh(self, *_) -> None:
        """
        Public callback used by feature controller to update panel's widgets' options.

        Concrete subclasses containing DropDown widgets dependent on dynamic inputs MUST
        implement this.
        """

    @staticmethod
    def _refresh_dropdown(
        dd: widgets.Dropdown,
        items: Sequence[Any],
        *,
        labeler: Callable[[Any], str] = str,
        default_first: bool = True,
        disable_widget: widgets.Widget | None = None
    ) -> None:
        """
        Populate `dd.options` with [(labeler(item), item), …].
        If empty, optionally disable `disable_widget`.
        """
        opts = [(labeler(it), it) for it in items]
        old = dd.value
        dd.options = opts

        # clear or reset value
        if not opts:
            dd.value = None
        elif default_first:
            if old not in {v for _, v in opts}:
                dd.value = opts[0][1]
        else:
            if old not in {v for _, v in opts}:
                dd.value = None

        if disable_widget:
            disable_widget.disabled = not bool(opts)
