#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Hydrostatic equilibrium calculations.

Created on Wed Aug 5 17:30:26 2026

@author: troy
"""

import math
import numpy as np

from meshmagick.mmio import load_MSH
from meshmagick.mesh import Mesh
from meshmagick import hydrostatics as hs


def calculate_hydrostatic_equilibrium(
    mesh_file,
    mass,
    cg_z,
    outer_radius,
    inner_radius=0.0,
    heave_radius=None,
    heave_thickness=None,
    water_density=1025.0,
    gravity=9.81,
    initial_translation=None,
    verbose=True,
):
    """
    Calculate the hydrostatic equilibrium position analytically and numerically.

    The analytic solution supports three simple geometries:

        1. Spar
           A vertical circular cylinder.

        2. Spar + heave plate
           A vertical spar attached to a larger, short cylindrical
           heave plate.

        3. Annulus
           A vertical annular cylinder.

    Meshmagick is then used to calculate the equilibrium position using
    the actual discretized mesh geometry.

    Parameters
    ----------
    mesh_file : str
        Path to the Gmsh .msh surface mesh.

    mass : float
        Total body mass [kg].

    cg_z : float
        Vertical center of gravity in the original mesh coordinate
        system [m].

    outer_radius : float
        Outer radius [m].

        For a spar or spar + heave plate, this is the spar radius.
        For an annulus, this is the annulus outer radius.

    inner_radius : float, optional
        Inner radius of an annulus [m].
        Default is 0.0.

    heave_radius : float or None, optional
        Radius of the heave plate [m].
        If provided, the body is treated analytically as a
        spar + heave plate.

    heave_thickness : float or None, optional
        Thickness of the heave plate [m].

    water_density : float, optional
        Water density [kg/m^3].
        Default is 1025 kg/m^3.

    gravity : float, optional
        Gravitational acceleration [m/s^2].
        Default is 9.81 m/s^2.

    initial_translation : float or None, optional
        Initial vertical translation used by Meshmagick [m].

        If None, the mesh is translated by -cg_z so that the center
        of gravity initially lies at z = 0.

    verbose : bool, optional
        Print Meshmagick iteration information, the analytic comparison,
        and the hydrostatic report.

    Returns
    -------
    dict
        Dictionary containing:

        geometry_type
            Analytic geometry used.

        analytic_draught
            Analytic equilibrium draught [m].

        numerical_draught
            Meshmagick equilibrium draught [m].

        draught_difference
            Numerical minus analytic draught [m].

        initial_translation
            Initial trial mesh translation [m].

        z_correction
            Additional translation calculated by Meshmagick [m].

        total_translation
            Total translation required to move the original mesh to
            hydrostatic equilibrium [m].

        equilibrium_cg_z
            Center of gravity after applying the total translation [m].

        hydrostatics
            Dictionary of Meshmagick hydrostatic properties.

        report
            Formatted Meshmagick hydrostatic report.
    """

    # ------------------------------------------------------------------
    # Check inputs
    # ------------------------------------------------------------------

    if mass <= 0.0:
        raise ValueError("Mass must be greater than zero.")

    if water_density <= 0.0:
        raise ValueError("Water density must be greater than zero.")

    if gravity <= 0.0:
        raise ValueError("Gravity must be greater than zero.")

    if outer_radius <= 0.0:
        raise ValueError("Outer radius must be greater than zero.")

    if inner_radius < 0.0:
        raise ValueError("Inner radius cannot be negative.")

    if inner_radius >= outer_radius:
        raise ValueError(
            "Inner radius must be smaller than outer radius."
        )

    if heave_radius is not None:
        if heave_radius <= outer_radius:
            raise ValueError(
                "Heave plate radius must be larger than the spar radius."
            )

        if heave_thickness is None or heave_thickness <= 0.0:
            raise ValueError(
                "A positive heave_thickness must be provided "
                "when heave_radius is specified."
            )

    # ------------------------------------------------------------------
    # Required displaced volume
    # ------------------------------------------------------------------
    #
    # Hydrostatic equilibrium requires:
    #
    #     F_b = W
    #
    #     rho * g * V_d = m * g
    #
    # Therefore:
    #
    #     V_d = m / rho
    #
    # Notice that gravity cancels from the equilibrium draught calculation.
    # It is still passed to Meshmagick because it is needed for quantities
    # such as hydrostatic stiffness.
    # ------------------------------------------------------------------

    displaced_volume = mass / water_density

    # ------------------------------------------------------------------
    # Analytic equilibrium draught
    # ------------------------------------------------------------------

    if heave_radius is not None:
        # --------------------------------------------------------------
        # Case 1: Spar + heave plate
        # --------------------------------------------------------------
        #
        # The heave plate occupies the lowest portion of the body.
        #
        # If the required displaced volume is smaller than the plate
        # volume, the waterline lies within the heave plate.
        #
        # Otherwise, the entire heave plate is submerged and the
        # remaining displaced volume is provided by the spar.
        # --------------------------------------------------------------

        geometry_type = "spar + heave plate"

        spar_area = math.pi * outer_radius**2
        heave_area = math.pi * heave_radius**2
        heave_volume = heave_area * heave_thickness

        if displaced_volume <= heave_volume:
            analytic_draught = displaced_volume / heave_area

        else:
            remaining_volume = displaced_volume - heave_volume

            analytic_draught = (
                heave_thickness
                + remaining_volume / spar_area
            )

    elif inner_radius > 0.0:
        # --------------------------------------------------------------
        # Case 2: Annulus
        # --------------------------------------------------------------

        geometry_type = "annulus"

        annulus_area = math.pi * (
            outer_radius**2 - inner_radius**2
        )

        analytic_draught = displaced_volume / annulus_area

    else:
        # --------------------------------------------------------------
        # Case 3: Spar
        # --------------------------------------------------------------

        geometry_type = "spar"

        spar_area = math.pi * outer_radius**2

        analytic_draught = displaced_volume / spar_area

    # ------------------------------------------------------------------
    # Load and heal the numerical mesh
    # ------------------------------------------------------------------

    vertices, faces = load_MSH(mesh_file)
    mesh = Mesh(vertices, faces)

    # Healing is important for hydrostatics because the surface normals
    # must be consistently oriented outward for the volume calculations.
    mesh.heal_mesh()

    # ------------------------------------------------------------------
    # Apply an initial trial translation
    # ------------------------------------------------------------------
    #
    # Meshmagick needs an initial configuration that intersects the
    # waterplane. By default, shift the body so that its COG lies at z = 0.
    # ------------------------------------------------------------------

    if initial_translation is None:
        initial_translation = -cg_z

    mesh.translate([0.0, 0.0, initial_translation])

    trial_cg_z = cg_z + initial_translation
    trial_cog = np.array([0.0, 0.0, trial_cg_z])

    # ------------------------------------------------------------------
    # Find the additional translation required for equilibrium
    # ------------------------------------------------------------------
    #
    # Meshmagick expects displacement mass in metric tonnes.
    # ------------------------------------------------------------------

    displacement_tonnes = mass / 1000.0

    z_correction = hs.displacement_equilibrium(
        mesh,
        displacement_tonnes,
        water_density,
        gravity,
        cog=trial_cog,
        verbose=verbose,
    )

    # Total translation relative to the ORIGINAL mesh coordinates.
    total_translation = initial_translation + z_correction

    # ------------------------------------------------------------------
    # Move the temporary Meshmagick model to equilibrium
    # ------------------------------------------------------------------
    #
    # This translation is only used to evaluate the final hydrostatics.
    # The calling program can independently apply total_translation to
    # the Capytaine mesh later.
    # ------------------------------------------------------------------

    mesh.translate([0.0, 0.0, z_correction])

    equilibrium_cg_z = cg_z + total_translation
    equilibrium_cog = np.array([0.0, 0.0, equilibrium_cg_z])

    # ------------------------------------------------------------------
    # Compute hydrostatic properties at equilibrium
    # ------------------------------------------------------------------

    hydrostatics = hs.compute_hydrostatics(
        mesh,
        equilibrium_cog,
        water_density,
        gravity,
    )

    numerical_draught = hydrostatics["draught"]
    draught_difference = numerical_draught - analytic_draught

    report = hs.get_hydrostatic_report(hydrostatics)

    # ------------------------------------------------------------------
    # Print results
    # ------------------------------------------------------------------

    if verbose:
        print()
        print("Equilibrium comparison")
        print("----------------------")
        print(f"Geometry:                    {geometry_type}")
        print(f"Body mass:                   {mass:.6f} kg")
        print(f"Required displaced volume:   {displaced_volume:.6f} m³")
        print()
        print(f"Analytic draught:            {analytic_draught:.6f} m")
        print(f"Meshmagick draught:          {numerical_draught:.6f} m")
        print(f"Draught difference:          {draught_difference:.6f} m")
        print()
        print(f"Initial translation:         {initial_translation:.6f} m")
        print(f"Meshmagick correction:       {z_correction:.6f} m")
        print(f"Total equilibrium shift:     {total_translation:.6f} m")
        print(f"Equilibrium COG z:           {equilibrium_cg_z:.6f} m")
        print()
        print(report)

    # ------------------------------------------------------------------
    # Return results
    # ------------------------------------------------------------------

    return {
        "geometry_type": geometry_type,
        "analytic_draught": analytic_draught,
        "numerical_draught": numerical_draught,
        "draught_difference": draught_difference,
        "displaced_volume": displaced_volume,
        "initial_translation": initial_translation,
        "z_correction": z_correction,
        "total_translation": total_translation,
        "equilibrium_cg_z": equilibrium_cg_z,
        "hydrostatics": hydrostatics,
        "report": report,
    }