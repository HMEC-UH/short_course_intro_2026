#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Aug 17 19:32:57 2026

@author: troy
"""

import numpy as np
import matplotlib.pyplot as plt

def radiation_plots(dataset, radiation_type='Added_Mass', dof='Heave'):
    """
    Plot a radiation coefficient for a selected degree of freedom.

    Parameters
    ----------
    dataset : xarray.Dataset
        Capytaine hydrodynamic results.
    radiation_type : str
        Radiation coefficient to plot:
        'Added_Mass' or 'Damping'.
    dof : str
        Degree of freedom to plot.
    """

    x = dataset.omega.data

    if radiation_type == 'Added_Mass':
        y = dataset.added_mass.sel(
            radiating_dof=dof,
            influenced_dof=dof,
        ).squeeze()

        label = 'Added Mass'
        unit = 'kg'

    elif radiation_type == 'Damping':
        y = dataset.radiation_damping.sel(
            radiating_dof=dof,
            influenced_dof=dof,
        ).squeeze()

        label = 'Radiation Damping'
        unit = 'kg/s'

    else:
        raise ValueError(
            f"Unknown radiation type: {radiation_type}"
        )

    fig, ax = plt.subplots()

    ax.plot(
        x,
        y,
        label=str(dataset.body_name.data),
    )

    ax.set_xlabel(r'$\omega$ (rad/s)', fontsize=16)
    ax.set_ylabel(f'{label} ({unit})', fontsize=16)

    ax.tick_params(axis='both', labelsize=14)

    ax.ticklabel_format(
        axis='y',
        style='plain',
        useOffset=False,
    )

    ax.legend(fontsize=14)

    plt.show()
    
def force_plots(
    dataset,
    force_type='Excitation',
    dof='Heave',
    wave_direction=0.0,
):
    """
    Plot the amplitude and phase of a wave-excitation force.

    Parameters
    ----------
    dataset : xarray.Dataset
        Capytaine hydrodynamic results.
    force_type : str
        Force to plot:
        'Froude_Krylov', 'Diffraction', or 'Excitation'.
    dof : str
        Degree of freedom to plot.
    wave_direction : float
        Wave direction in radians.
    """

    omega = dataset.omega.data

    if force_type == 'Froude_Krylov':
        force = dataset.Froude_Krylov_force
        label = 'Froude-Krylov Force'

    elif force_type == 'Diffraction':
        force = dataset.diffraction_force
        label = 'Diffraction Force'

    elif force_type == 'Excitation':
        force = dataset.excitation_force
        label = 'Excitation Force'

    else:
        raise ValueError(
            f"Unknown force type: {force_type}"
        )

    # Select degree of freedom and wave direction
    force = force.sel(
        influenced_dof=dof,
        wave_direction=wave_direction,
    ).squeeze()

    # Calculate amplitude and phase
    amplitude = np.abs(force)
    phase = np.angle(force, deg=True)

    # -------------------------------------------------------------------------
    # Plot
    # -------------------------------------------------------------------------
    fig, (ax1, ax2) = plt.subplots(
        2,
        1,
        sharex=True,
        figsize=(8, 8),
    )

    # Amplitude
    ax1.plot(omega, amplitude)

    ax1.set_ylabel('Force Amplitude (N)', fontsize=16)
    ax1.tick_params(axis='both', labelsize=14)

    ax1.ticklabel_format(
        axis='y',
        style='plain',
        useOffset=False,
    )

    ax1.set_title(label, fontsize=16)

    # Phase
    ax2.plot(omega, phase)

    ax2.set_xlabel(r'$\omega$ (rad/s)', fontsize=16)
    ax2.set_ylabel('Phase (deg)', fontsize=16)
    ax2.tick_params(axis='both', labelsize=14)

    ax2.set_ylim(-185, 185)
    ax2.set_yticks([-180, -90, 0, 90, 180])

    fig.tight_layout()

    plt.show()