# -*- coding: utf-8 -*-

# -------------------------- Preprocessing Directives -------------------------

# Standard Libraries
import logging as lg
# import os as os
from sys import exit

# 3rd Party packages
from datetime import datetime

# import matplotlib.pyplot as plt
import numpy as np

# My packages/Header files
# Here

# ----------------------------- Program Information ----------------------------

"""
A TEMPORARY location to collate my physics functions from across the existing ipynb files. I can then
create a more cohesive package for these when I have time
"""
PROGRAM_NAME = "custom_physics_equations.py"
"""
Created on 24 Jul 24 by Cameron Aidan McEleney
"""


# ---------------------------- Function Declarations ---------------------------

def loggingSetup():
    """
    Minimum Working Example (MWE) for logging. Pre-defined levels are:
        
        Highest               ---->            Lowest
        CRITICAL, ERROR, WARNING, INFO, DEBUG, NOTSET
    """
    today_date = datetime.now().strftime("%y%m%d")
    current_time = datetime.now().strftime("%H%M")

    lg.basicConfig(filename=f'./{today_date}-{current_time}.log',
                   filemode='w',
                   level=lg.INFO,
                   format='%(asctime)s | %(module)s::%(funcName)s | %(levelname)s | %(message)s',
                   datefmt='%Y-%m-%d %H:%M:%S',
                   force=True)


# ------------------------------ Implementations ------------------------------

def gilbert_pbc_exponential_grad(pos, alpha, system_prop, system_subregions) -> float:
    """
    Employs an exponential gradient across a Periodic Boundary Condition (PBC) region by normalising the passed min/max
    Gilbert Damping Factor (alpha) values.
    :param pos: Position of current cell in the mesh

    :return: Alpha value
    """

    # current positions
    x, y, z = pos  # spatial coordinates
    xn, yn, zn = (coord * 1e9 for coord in pos)  # cell coordinates

    # min and max cell coordinates of system
    xmin, ymin, zmin = (p1_val * 1e9 for p1_val in system_prop.p1)
    xmax, ymax, zmax = (p2_val * 1e9 for p2_val in system_prop.p2)

    # A.B.C. widths
    derived_widths_lhs = [int(val / system_subregions.dampingLhs.region.multiplier) for val in
                          system_subregions.dampingLhs.region.edges]

    widths = {'x': derived_widths_lhs[0], 'y': derived_widths_lhs[1], 'z': derived_widths_lhs[2]}

    # left (a) and right (b) bounds of the A.B.C. region
    xa, ya, za = xmin + widths['x'], ymin + widths['y'], zmin + widths['z']
    xb, yb, zb = xmax - widths['x'], ymax - widths['y'], zmax - widths['z']

    # Scales damping between [alpha, 1.0]
    if xn <= xa:
        return np.exp(((xmin - xn) * np.log(alpha)) / (xmin - xa))
    elif xn >= xb:
        return np.exp(((xmax - xn) * np.log(alpha)) / (xmax - xb))
    else:
        return alpha


def calculate_demag_factor_uniform_prism(length, width, thickness, alignment='z'):
    demag_factors = {'N_x': -1, 'N_y': -1, 'N_z': -1}

    def _calculate_demag_factor(a, b, c):
        r = a**2 + b**2 + c**2

        demag_factor = ((b ** 2 - c ** 2) / (2 * b * c)) * np.log((np.sqrt(r) - a)
                                                                  / (np.sqrt(r) + a))

        demag_factor += ((a ** 2 - c ** 2) / (2 * a * c)) * np.log((np.sqrt(r) - b)
                                                                   / (np.sqrt(r) + b))

        demag_factor += (b / (2 * c)) * np.log((np.sqrt(a ** 2 + b ** 2) + a)
                                               / (np.sqrt(a ** 2 + b ** 2) - a))

        demag_factor += (a / (2 * c)) * np.log((np.sqrt(a ** 2 + b ** 2) + b)
                                               / (np.sqrt(a ** 2 + b ** 2) - b))

        demag_factor += (c / (2 * a)) * np.log((np.sqrt(b ** 2 + c ** 2) - b)
                                               / (np.sqrt(b ** 2 + c ** 2) + b))

        demag_factor += (c / (2 * b)) * np.log((np.sqrt(a ** 2 + c ** 2) - a)
                                               / (np.sqrt(a ** 2 + c ** 2) + a))

        demag_factor += 2 * np.arctan((a * b) / (c * np.sqrt(r)))

        demag_factor += (a ** 3 + b ** 3 - 2 * c ** 3) / (3 * a * b * c)

        demag_factor += ((a ** 2 + b ** 2 - 2 * c ** 2) / (3 * a * b * c)) * np.sqrt(r)

        demag_factor += (c / (a * b)) * (np.sqrt(a ** 2 + c ** 2) + np.sqrt(b ** 2 + c ** 2))

        demag_factor -= ((np.power((a ** 2 + b ** 2), 3 / 2) + np.power((b ** 2 + c ** 2), 3 / 2) + np.power(
            (c ** 2 + a ** 2), 3 / 2))
                         / (3 * a * b * c))

        demag_factor /= np.pi

        return demag_factor

    if alignment.upper() == 'Z':
        demag_factors['N_z'] = _calculate_demag_factor(length, width, thickness)
        demag_factors['N_y'] = _calculate_demag_factor(thickness, length, width)
        demag_factors['N_x'] = _calculate_demag_factor(width, thickness, length)
    else:
        raise ("custom_physics_equations.py -> calculate_demag_factor_uniform_prism -> _calculate_demag_factor: "
               "Unknown parameter [alignment] was passed")

    N_total = 0
    for k, v in demag_factors.items():
        N_total += v
    if N_total >= 1 + 1e-4:
        exit(1)

    return demag_factors
