#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Project: Ubermag
Path:    include/Uberwidgets/user_interface/builder.py

Description:
    Short description of what this (builder.py) does.
    
Author:      Cameron Aidan McEleney < c.mceleney.1@research.gla.ac.uk >
Created:     25 Apr 2025
IDE:         PyCharm
Version:     0.1.0
"""

# Standard library imports
from ipywidgets import Tab, Button, Output, VBox, Layout
from IPython.display import display
from typing import Optional, Callable, Tuple, Dict, Any

# Third-party imports

# Local application imports
from .energy_tab   import make_energy_tab
from .material_tab import make_material_tab
from .time_tab     import make_time_tab
from .dynamic_tab  import make_dynamic_tab

from ..metadata.enable_energy_terms import EnableEnergyTerms
from ..metadata.enable_simulation_params import EnableSimulationParameters
from Uberwidgets.metadata.descriptors import _dmi_desc


__all__ = ["build_simulation_ui"]


def build_simulation_ui(
        energy_model: EnableEnergyTerms = EnableEnergyTerms(),
        on_confirm: Optional[Callable[[EnableEnergyTerms,
                                       EnableSimulationParameters,
                                       Dict[str, Any]], None]] = None,
) -> Tuple[
    EnableEnergyTerms,
    EnableSimulationParameters,
    Dict[str, Any],
    Button,
    Output
]:
    """
    Build and display the full simulation UI.

    Parameters
    ----------
    energy_model:
        Allows the user to directly provide their own energy model.

    on_confirm : callable, optional
        If provided, will be called after “Instantiate all” is clicked,
        with arguments (energy_model, sim_model, overrides).

    Returns
    -------
    energy_model : EnableEnergyTerms
        The energy‐term flags model (populated with user choices).
    sim_model : EnableSimulationParameters
        The simulation parameters model (populated with user choices).
    overrides : dict
        Any on-the-fly overrides collected in the “Advanced” tab.
    btn : Button
        The “Instantiate all” button widget.
    out : Output
        The output area where the final models are printed.
    """
    # Initialize models
    sim_model    = EnableSimulationParameters()

    # 2) Build each tab and grab their widget maps
    e_acc, e_wgmap = make_energy_tab(energy_model)
    m_acc, m_wgmap = make_material_tab(sim_model)
    t_acc, t_wgmap = make_time_tab(sim_model)
    d_acc, d_wgmap = make_dynamic_tab(sim_model)

    # 3) Assemble top-level Tab container
    tab = Tab(children=[
        VBox([e_acc, m_acc]),
        VBox([t_acc, d_acc]),
    ])
    tab.set_title(0, 'Magnetic properties')
    tab.set_title(1, 'Time controls')

    # 4) Instantiate button + output area
    btn = Button(
        description='Instantiate all',
        button_style='primary',
        layout=Layout(margin='10px')
    )
    out = Output()

    # Pull the dynamic overrides dict from the widget map
    overrides: Dict[str, Any] = d_wgmap.get('overrides', {})

    # 5) Callback to update models from widget values
    def on_instantiate(_):
        # update energy_model
        for name, wg in e_wgmap.items():
            if name in ('enable_dmi', 'dmi_method'):
                continue
            setattr(energy_model, name, wg.value)

        # handle DMI via the descriptor
        if e_wgmap['enable_dmi'].value:
            energy_model.dmi = {
                k: (e_wgmap['dmi_method'].value == k)
                for k in _dmi_desc._dmi_flags
            }
        else:
            energy_model.dmi = False

        # update sim_model from material & time widgets
        for wgmap in (m_wgmap, t_wgmap):
            for name, wg in wgmap.items():
                setattr(sim_model, name, wg.value)

        # apply any dynamic overrides
        for name, val in overrides.items():
            setattr(sim_model, name, val)

        # display final state and call confirmation hook
        with out:
            out.clear_output()
            print('Energy settings:', energy_model)
            print('Simulation params:', sim_model)
        if on_confirm:
            on_confirm(energy_model, sim_model, overrides)

    btn.on_click(on_instantiate)

    # 6) Display everything
    display(tab, btn, out)

    # 7) Return models, overrides, and widgets for further use
    return energy_model, sim_model, overrides, btn, out