#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Jun 23 15:20:37 2026

@author: troy
"""

import capytaine as cpt
import numpy as np
import xarray as xr
import matplotlib.pyplot as plt


# --------------------------
# 1. Configuration
# --------------------------
# Console output level to get more details about what Capytaine is doing
# options: 'INFO' or 'DEBUG' or 'WARNING' (default)
cpt.set_logging('WARNING')

# Density
RHO = 1025

# Parallel
Njobs = 8

# Define solver
solver = cpt.BEMSolver()

# --------------------------
# 2. User inputs
# --------------------------
# Define wave periods of interest
Period_min = 0.4
Period_max = 25
Period_N = 36

# Wave direction
wave_dir = 0

# Water depth
water_depth = 500

# Center of gravity and center of rotation
cg = -4.0
cr = cg

# File name
fname = 'spar_buoy'

# ----------------------------
# 3. Define frequency domain
# ----------------------------
omega_max = 2*np.pi / Period_min
omega_min = 2*np.pi / Period_max
omega = np.linspace(omega_min,omega_max,Period_N)
T = 2*np.pi / omega


# -------------------------------
# 4. Generate body
# -------------------------------
# Load the mesh
mesh_input = cpt.load_mesh('../Gmsh/spar_buoy.msh',file_format='gmsh')
mesh_input.show_matplotlib()

# Position the mesh w/ reference to the still water level
mesh_input.translate_z(-5)

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
    center_of_mass=(0, 0, cg),
    dofs={}
).immersed_part()
body.show_matplotlib()

# Append/overwrite definitions
body.rotation_center = (0, 0, cr)  # The rotation_center is used for the definition of the rotation dofs
body.name = fname # Redefine the body name

# If the mass is not specified (as in the examples above), the body is
# assumed to be in buoyancy equilibrium. It’s mass is the mass of the
# displaced volume of water.
#
# Non-neutrally buoyant bodies are partially implemented (only for a single
# rigid body). In this case, the mass of the body can be given by setting the
# mass attribute
# self.body.mass = 43.344;

# Define DOFs
#body.add_translation_dof(direction=[1, 0, 0], name='Surge')
#body.add_translation_dof(direction=[0, 1, 0], name='Sway')
body.add_translation_dof(direction=[0, 0, 1], name='Heave')
#body.add_rotation_dof(axis=cpt.Axis(point=body.rotation_center, vector=(1, 0, 0)), name="Roll")
#body.add_rotation_dof(axis=cpt.Axis(point=body.rotation_center, vector=(0, 1, 0)), name="Pitch")
#body.add_rotation_dof(axis=cpt.Axis(point=body.rotation_center, vector=(0, 0, 1)), name="Yaw")

# -------------------------------
# 5. Hydrostatic analysis
# -------------------------------
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
output_file1 = f"Hydrostatics_{body.name}.dat"
with open(output_file1, 'w') as f:
    for j in [0, 1, 2]:
        line = f'XF = {cb[j]:7.3f} - XG = {cg[j]:7.3f} \n'
        f.write(line)
    line = f'Displacement = {vo:E}'
    f.write(line)

# 2 - stiffness coefficients
output_file2 = f"KH_{body.name}.dat"
np.savetxt(output_file2, body.hydrostatic_stiffness.data)

# Hydrostatic summary
print("\nStiffness Matrix:")
for row in body.hydrostatic_stiffness:
    print("  ".join(f"{val:10.8f}" for val in row))

print("\nInertia Matrix:")
for row in body.inertia_matrix:
    print("  ".join(f"{val:10.8f}" for val in row))


# -------------------------------
# 6. Hydrodynamic analysis
# -------------------------------
# Build "test matrix"
test_matrix = xr.Dataset(coords={
    'omega': ('omega',omega),                          # list of angular frequencies to be run
    'wave_direction': ('wave_direction',[wave_dir]),     # list of angles to be run (radians)
    'radiating_dof': list(body.dofs),                  # take list of dofs to be run from 1st body
    'water_depth': ('water_depth',[water_depth]),              # list of depths to be run
})

dataset = solver.fill_dataset(test_matrix, body, n_jobs=Njobs)


x = dataset.omega.data
#iRow = np.where(dataset.radiating_dof.data == 'heave')[0][0]
#kCol = np.where(dataset.influenced_dof.data == 'heave')[0][0]
iRow = np.where(dataset.radiating_dof.data == 'Heave')
kCol = np.where(dataset.influenced_dof.data == 'Heave')

radiation_type = 'Added_Mass'
if radiation_type == 'Added_Mass':
    label = 'Added Mass Coeffs'
    unit = 'kg'
    
    y_list = [dataset.added_mass.data[:, iRow, kCol].squeeze()]
    name_list = [dataset.body_name.data]
            
elif radiation_type == 'Damping':
    label = 'Damping Coeffs'
    unit = '?'

    y_list = [dataset.radiation_damping.data[:, iRow, kCol].squeeze()]
    name_list = [dataset.body_name.data]

else:
    raise ValueError(f"Unknown force type: {radiation_type}")

plt.figure()
for y, name in zip(y_list, name_list):
    print(np.ndim(y))
    plt.plot(x,y,label=name)

plt.xlabel('$\omega$ (rad/s)')
plt.ylabel(f'{label} ({unit})')
plt.legend()
plt.show()
        

