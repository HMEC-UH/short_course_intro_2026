#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Jun 23 15:20:37 2026

@author: troy
"""

import numpy as np
import xarray as xr

import capytaine as cpt
from capytaine.io.mesh_writers import write_STL

import matplotlib.pyplot as plt

from functions.calculate_draft import calculate_hydrostatic_equilibrium
from functions.mesh_plots import plot_mesh_profile
from functions.animate_body import animate_body, rao_animation
from functions.plot_analysis import radiation_plots, force_plots

# =============================================================================
# 1. CONFIGURE
# =============================================================================
# Console output level to get more details about what Capytaine is doing
# options: 'INFO' or 'DEBUG' or 'WARNING' (default)
cpt.set_logging('WARNING')

# Density
RHO = 1025.0

# Gravity
G = 9.81

# Parallel
Njobs = 8

# Define solver
solver = cpt.BEMSolver()

# =============================================================================
# 2. USER-DEFINED PARAMETERS
# =============================================================================
# Define wave periods of interest
Period_min = 1
Period_max = 20
Period_N = 36

# Wave direction
wave_dir = 0

# Water depth
water_depth = 500

# Plot type
radiation_type = 'Added_Mass'
#radiation_type = 'Damping'

# Spar properties
spar_radius = 0.0301625         # Cylinder radius [m] (2.375" dia)
spar_mass = 7.166759            # (kg)
spar_cg = 3.048                 # Z - Center of gravity (m)

# Heave plate properties
plate_radius = 0.3048           # Heave-plate radius [m]
plate_thickness = 0.009525      # Heave-plate thickness [m]
heave_mass = 3.810176           # (kg)
heave_cg = 0.0047625            # Z - Center of gravity (m)

# Ballast properties
ballast_mass = 9.071847         # (kg)
ballast_mass = 7.25748
ballast_cg = 0.0762             # Z - Center of gravity (m)

# Float properties
annulus_outer_radius = 0.483    # Cylinder height [m] (19 in)
annular_mass = 4.535924         # (kg)
annular_cg = 0.1525             # Z - Center of gravity (m)
annulus_height = 0.305          # Cylinder height [m]

# Directories
mesh_dir = '../../Gmsh/meshes/'
output_dir = '../output/'

# Bodies
analysis = 'spar_heave'

if analysis == 'spar':
    body1_mesh = mesh_dir + 'spar_buoy_refined.msh'

    body1_mass = spar_mass + ballast_mass
    body1_cg = (spar_mass * spar_cg
                + ballast_mass * ballast_cg
                ) / body1_mass

    outer_radius = spar_radius
    inner_radius = 0.0
    heave_radius = None
    heave_thickness = None


elif analysis == 'spar_heave':
    body1_mesh = mesh_dir + 'spar_with_heave_plate.msh'

    body1_mass = spar_mass + ballast_mass + heave_mass
    body1_cg = (
        spar_mass * spar_cg
        + ballast_mass * ballast_cg
        + heave_mass * heave_cg
    ) / body1_mass

    outer_radius = spar_radius
    inner_radius = 0.0
    heave_radius = plate_radius
    heave_thickness = plate_thickness


elif analysis == 'annulus':
    body1_mesh = mesh_dir + 'annular_body.msh'

    body1_mass = annular_mass
    body1_cg = annular_cg

    outer_radius = annulus_outer_radius
    inner_radius = spar_radius
    heave_radius = None
    heave_thickness = None


else:
    raise ValueError(f"Unknown analysis type: {analysis}")


# Determine hydrostatic equilibrium
results = calculate_hydrostatic_equilibrium(
    mesh_file=body1_mesh,
    mass=body1_mass,
    cg_z=body1_cg,
    outer_radius=outer_radius,
    inner_radius=inner_radius,
    heave_radius=heave_radius,
    heave_thickness=heave_thickness,
    water_density=RHO,
    gravity=G,
)

print(f"Analytic draft:   {results['analytic_draught']:.6f} m")
print(f"Numerical draft:  {results['numerical_draught']:.6f} m")
print(f"Difference:       {results['draught_difference']:.6f} m")


# Translation required to place the original mesh at equilibrium
dz_hydrostatic = results["total_translation"]

# COG location after the same translation
cg_hydrostatic = results["equilibrium_cg_z"]


# =============================================================================
# 3. DEFINE FREQUENCY DOMAIN
# =============================================================================
omega_max = 2*np.pi / Period_min
omega_min = 2*np.pi / Period_max
omega = np.linspace(omega_min,omega_max,Period_N)
T = 2*np.pi / omega


# =============================================================================
# 4. GENERATE BODY
# =============================================================================

# Load the mesh
mesh_input = cpt.load_mesh(body1_mesh,file_format='gmsh')

# Position the mesh w/ reference to the still water level
mesh_input.translate_z(dz_hydrostatic)

# Save full body mesh for animations
full_body = cpt.FloatingBody(
    mesh=mesh_input,
    center_of_mass=(0, 0, cg_hydrostatic),
    dofs={},
    name='full_body_1'
)

full_body.add_translation_dof(direction=[0, 0, 1], name='Heave')

# Check equilibrium position
plot_mesh_profile(
    mesh_input,
    cg_z=cg_hydrostatic,
)

# Generate mesh lid
lid_depth = mesh_input.lowest_lid_position(omega_max)
lid_mesh = mesh_input.generate_lid(z = lid_depth) 

# NOTES:
#   - Before computing individual hydrostatic parameters, make sure to crop
#     the body to only keep the immersed part.
#   - The center_of_mass is used for some hydrostatics properties but not
#     required for the diffraction-radiation problems.
body = cpt.FloatingBody(
    mesh=mesh_input,
    lid_mesh=lid_mesh,
    center_of_mass=(0, 0, cg_hydrostatic),
    dofs={},
    name='body_1'
).immersed_part()

# Append/overwrite definitions
body.rotation_center = (0, 0, cg_hydrostatic)  # The rotation_center is used for the definition of the rotation dofs

# Visualize the body
body.show_matplotlib()

ax = plt.gca()
ax.view_init(elev=0, azim=-90)
ax.set_proj_type("ortho")

# If the mass is not specified (as in the examples above), the body is
# assumed to be in buoyancy equilibrium. It’s mass is the mass of the
# displaced volume of water.
#
# Non-neutrally buoyant bodies are partially implemented (only for a single
# rigid body). In this case, the mass of the body can be given by setting the
# mass attribute
#
# self.body.mass = 43.344;

# Define DOFs
#body.add_translation_dof(direction=[1, 0, 0], name='Surge')
#body.add_translation_dof(direction=[0, 1, 0], name='Sway')
body.add_translation_dof(direction=[0, 0, 1], name='Heave')
#body.add_rotation_dof(axis=cpt.Axis(point=body.rotation_center, vector=(1, 0, 0)), name="Roll")
#body.add_rotation_dof(axis=cpt.Axis(point=body.rotation_center, vector=(0, 1, 0)), name="Pitch")
#body.add_rotation_dof(axis=cpt.Axis(point=body.rotation_center, vector=(0, 0, 1)), name="Yaw")

# Capytaine (to compare w/ Meshmagick)
print("Volume:", body.volume)
print("Center of buoyancy:", body.center_of_buoyancy)
print("Wet surface area:", body.wet_surface_area)
print("Displaced mass:", body.disp_mass(rho=1025))
print("Waterplane center:", body.waterplane_center)
print("Waterplane area:", body.waterplane_area)
print("Metacentric parameters:",
    body.transversal_metacentric_radius,
    body.longitudinal_metacentric_radius,
    body.transversal_metacentric_height,
    body.longitudinal_metacentric_height)


# =============================================================================
# 5. HYDROSTATIC ANALYSIS
# =============================================================================
hydrostatics = body.compute_hydrostatics(rho=RHO)

# Append the hydrostatics to the body and call out the matrices for 
# inertia and stiffness to be utilized in later processing.
body.hydrostatics = hydrostatics
body.inertia_matrix = hydrostatics['inertia_matrix']
body.hydrostatic_stiffness = hydrostatics['hydrostatic_stiffness']


# Variables of interest (see "hydrostatics.keys()")
vo = hydrostatics['disp_volume']
cg = hydrostatics['center_of_mass']
cb = hydrostatics['center_of_buoyancy']

# Files needed by BEMIO in WEC-Sim
# 1 - center of gravity and buoyancy
output_file1 = f"{output_dir}Hydrostatics_{analysis}.dat"
with open(output_file1, 'w') as f:
    for j in [0, 1, 2]:
        line = f'XF = {cb[j]:7.3f} - XG = {cg[j]:7.3f} \n'
        f.write(line)
    line = f'Displacement = {vo:E}'
    f.write(line)

# 2 - stiffness coefficients
output_file2 = f"{output_dir}KH_{analysis}.dat"
np.savetxt(output_file2, body.hydrostatic_stiffness.data)

# 3 - STL file
output_file3 = f"{output_dir}{analysis}.stl"
write_STL(output_file3,
          mesh_input.vertices,
          mesh_input.faces
)

# Hydrostatic summary
print("\nStiffness Matrix:")
for row in body.hydrostatic_stiffness:
    print("  ".join(f"{val:10.8f}" for val in row))

print("\nInertia Matrix:")
for row in body.inertia_matrix:
    print("  ".join(f"{val:10.8f}" for val in row))


# =============================================================================
# 5. HYDRODYNAMIC ANALYSIS
# =============================================================================
# Build "test matrix"
test_matrix = xr.Dataset(coords={
    'omega': ('omega',omega),                          # list of angular frequencies to be run
    'wave_direction': ('wave_direction',[wave_dir]),     # list of angles to be run (radians)
    'radiating_dof': list(body.dofs),                  # take list of dofs to be run from 1st body
    'water_depth': ('water_depth',[water_depth]),              # list of depths to be run
})

dataset = solver.fill_dataset(test_matrix, body, n_jobs=Njobs)


# =============================================================================
# 6. PLOTS
# =============================================================================

radiation_plots(
    dataset,
    radiation_type='Damping',
    dof='Heave',
)

radiation_plots(
    dataset,
    radiation_type='Added_Mass',
    dof='Heave',
)

force_plots(
    dataset,
    force_type='Froude_Krylov',
    dof='Heave',
    wave_direction=wave_dir,
)

force_plots(
    dataset,
    force_type='Diffraction',
    dof='Heave',
    wave_direction=wave_dir,
)

force_plots(
    dataset,
    force_type='Excitation',
    dof='Heave',
    wave_direction=wave_dir,
)

# =============================================================================
# 7. ANIMATIONS
# =============================================================================
# Create full body mesh for animations
animate_body(solver,full_body,body)

full_body.hydrostatics = hydrostatics
full_body.inertia_matrix = hydrostatics['inertia_matrix']
full_body.hydrostatic_stiffness = hydrostatics['hydrostatic_stiffness']
rao_animation(solver,full_body)
