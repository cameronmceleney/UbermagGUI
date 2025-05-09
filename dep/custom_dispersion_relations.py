# -*- coding: utf-8 -*-

# -------------------------- Preprocessing Directives -------------------------

# Standard Libraries
import logging as lg
# import os as os
from sys import exit

# 3rd Party packages
from datetime import datetime
import micromagneticmodel as mm

# import matplotlib.pyplot as plt
import numpy as np
import custom_physics_equations as cpe

# ----------------------------- Program Information ----------------------------

"""
Description of what foo.py does
"""
PROGRAM_NAME = "foo.py"
"""
Created on (date) by (author)
"""


# ---------------------------- Function Declarations ---------------------------

def Omega_Moon(H0, Ms, A, D, k, d, gamma, p=1, demag=1, has_dmi=1):
    mu0 = 4 * np.pi * 1e-7
    J = 2 * A / (mu0 * Ms)
    DM = -2 * D / (mu0 * Ms)

    om = np.sqrt((H0 + 0.25 * Ms + J * (k ** 2)) * (H0 + 3 * Ms * 0.25 + J * (k ** 2))
                 - (1 + 2 * np.exp(2 * abs(k) * d)) * np.exp(-4 * abs(k) * d) * (Ms ** 2) / 16
                 )
    om += p * DM * k

    # the mu0 factor shown in the paper is not necessary if we use gamma
    # in Hz / (A / m)
    om = gamma * mm.consts.mu0 * om

    return om


# 0.14242684543643974, 0.8574134059681958
def Omega_Moon_large_k(H0, Ms, A, D, k, d, gamma, p=1, demag=1, has_dmi=1):
    J = 2 * A / (mm.consts.mu0 * Ms)
    DM = 2 * D / (mm.consts.mu0 * Ms)

    om = np.sqrt((H0 + J * (k ** 2)) * (H0 + demag * Ms + J * (k ** 2)))
    om += p * DM * k * has_dmi

    # the mu0 factor shown in the paper is not necessary if we use gamma
    # in Hz / (A / m)
    om *= (gamma * mm.consts.mu0)

    return om


def Omega_Moon_small_k(H0, Ms, A, D, k, d, gamma, p=1, demag=1, has_dmi=1):
    J = 2 * A / (mm.consts.mu0 * Ms)
    DM = 2 * D / (mm.consts.mu0 * Ms)

    om = np.sqrt(H0 * (H0 + demag * Ms)) + ((Ms ** 2) + abs(k) * d) / (4 * np.sqrt(H0 * (H0 + demag * Ms)))
    om += p * DM * k * has_dmi

    # the mu0 factor shown in the paper is not necessary if we use gamma
    # in Hz / (A / m)
    om *= (gamma * mm.consts.mu0)

    return om


def Omega_Moon_custom(H0, Ms, A, D, k, d, gamma, p=1, demag=1, has_dmi=1):
    J = 2 * A / (mm.consts.mu0 * Ms)
    DM = 2 * D / (mm.consts.mu0 * Ms)

    Nx = 0
    Ny = 0.5
    Nz = 0.5

    om = np.sqrt((H0 + J * (k ** 2) + Ms * (Nx - Nz)) * (H0 + J * (k ** 2) + Ms * (Ny - Nz)))
    om += p * DM * k * has_dmi

    # the mu0 factor shown in the paper is not necessary if we use gamma
    # in Hz / (A / m)
    om *= (gamma * mm.consts.mu0)

    return om


def Omega_generalised(system_prop, H0, Ms, A, D, k, d, gamma, p=1, has_demag=1, has_dmi=1):
    J = 2 * A / (mm.consts.mu0 * Ms)
    DM = -2 * D / (mm.consts.mu0 * Ms)

    demag_factors = cpe.calculate_demag_factor_uniform_prism(system_prop.length - 2e-9,
                                                             system_prop.width,
                                                             system_prop.thickness)
    # print(demag_factors)

    om = np.sqrt((H0 + J * (k ** 2) + has_demag * Ms * (demag_factors['N_x'] - demag_factors['N_z']))
                 * (H0 + J * (k ** 2) + has_demag * Ms * (demag_factors['N_y'] - demag_factors['N_z']))
                 )

    om += p * DM * k * has_dmi

    # the mu0 factor shown in the paper is not necessary if we use gamma
    # in Hz / (A / m)
    om *= (gamma * mm.consts.mu0)

    return om


def Omega_generalised_with_ua(system_prop, H0, Ms, A, D, k, d, K1, K2, aniso_axis, gamma, p=1,
                              has_demag=1, has_dmi=1, has_aniso=1):
    J = 2 * A / (mm.consts.mu0 * Ms)
    DM = -2 * D / (mm.consts.mu0 * Ms)

    demag_factors = cpe.calculate_demag_factor_uniform_prism(system_prop.length - 2e-9,
                                                             system_prop.width,
                                                             system_prop.thickness)
    # print(demag_factors)

    #om = np.sqrt((H0 + J * (k ** 2) + has_demag * Ms * (demag_factors['N_x'] - demag_factors['N_z']))
    #             * (H0 + J * (k ** 2) + has_aniso * ((4 * aniso_axis[2] ** 2) / (Ms * mm.consts.mu0)
    #                                                 * (K1 + 2 * K2 * aniso_axis[2] ** 2))
    #                + has_demag * Ms * (demag_factors['N_y'] - demag_factors['N_z'])
    #                )
    #             + has_aniso * (4 * aniso_axis[2] ** 4) / (Ms ** 2 * mm.consts.mu0 ** 2)
    #             * (1 * K1 ** 2 + 4 * K1 * K2 * aniso_axis[2] ** 2 + 4 * K2 ** 2 * aniso_axis[2] ** 2)
    #             )

    om = np.sqrt((H0
                  + J * (k ** 2)
                  + has_aniso * ((2 * (aniso_axis[2] ** 2)) / (Ms * mm.consts.mu0)
                                 * (K1 + 2 * K2 * aniso_axis[2] ** 2))
                  + has_demag * Ms * (demag_factors['N_x'] - demag_factors['N_z']))
                 * (H0
                    + J * (k ** 2)
                    + has_aniso * ((2 * (aniso_axis[2] ** 2)) / (Ms * mm.consts.mu0)
                                   * (K1 + 2 * K2 * aniso_axis[2] ** 2))
                    + has_demag * Ms * (demag_factors['N_y'] - demag_factors['N_z'])
                    )
                 )

    om += has_dmi * p * DM * k

    # the mu0 factor shown in the paper is not necessary if we use gamma
    # in Hz / (A / m)
    om *= (gamma * mm.consts.mu0)

    return om
