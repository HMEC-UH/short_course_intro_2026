#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu May 28 10:09:44 2026

@author: troy
"""

import gmsh

# ------------------------------------------------------------
# 1. Initialize Gmsh
# ------------------------------------------------------------
# This starts the Gmsh Python API. It must be called before using
# any Gmsh functions.
gmsh.initialize()

# Give the model a name. This is useful when working with
# multiple geometries or when inspecting output files.
gmsh.model.add("spar_buoy")

# ------------------------------------------------------------
# 2. Define cylinder parameters
# ------------------------------------------------------------
# For this first example, we define a simple vertical cylinder
# representing a spar. All dimensions are specified in meters.
#
# The cylinder axis will point in the positive z-direction.

spar_radius = 0.089/2      # Cylinder radius [m] (0.089 m ~ 3.5 in)
spar_height = 6.096      # Cylinder height [m] (6.096 m ~ 20 ft)

# The cylinder is defined by:
#   - the center of the first circular face: (x, y, z)
#   - an axis vector: (dx, dy, dz)
#   - a radius
#
# Here, the first circular face is centered at z = 0,
# and the cylinder extends upward to z = spar_height.
#
# These coordinates define the geometry within a local
# reference frame whose origin is located at (0, 0, 0).

spar_x0 = 0.0
spar_y0 = 0.0
spar_z0 = 0.0

spar_dx = 0.0
spar_dy = 0.0
spar_dz = spar_height

# ------------------------------------------------------------
# 3. Create the cylinder geometry
# ------------------------------------------------------------
# Gmsh includes multiple geometry kernels. Here we use the
# OpenCASCADE kernel, accessed through gmsh.model.occ.
#
# addCylinder returns an integer tag identifying the new volume.

cylinder = gmsh.model.occ.addCylinder(
    spar_x0, spar_y0, spar_z0,
    spar_dx, spar_dy, spar_dz,
    spar_radius
)

# ------------------------------------------------------------
# 4. Synchronize the geometry
# ------------------------------------------------------------
# After creating geometry with the OpenCASCADE kernel, we must
# synchronize it with the main Gmsh model before meshing.

gmsh.model.occ.synchronize()

# ------------------------------------------------------------
# 5. Set mesh size
# ------------------------------------------------------------
# This controls the approximate size of mesh elements.
# Smaller values create a finer mesh; larger values create
# a coarser mesh.

mesh_size = 0.03

gmsh.option.setNumber("Mesh.CharacteristicLengthMin", mesh_size)
gmsh.option.setNumber("Mesh.CharacteristicLengthMax", mesh_size)

# ------------------------------------------------------------
# 6. Generate the mesh
# ------------------------------------------------------------
# We will be most interested in the surface (2) mesh of the body rather than
# the full volume (3) mesh.

gmsh.model.mesh.generate(2)

# ------------------------------------------------------------
# 7. Write the mesh to a file
# ------------------------------------------------------------
# The .msh format is Gmsh's native mesh format.

gmsh.write("spar_buoy.msh")

# ------------------------------------------------------------
# 8. Finalize Gmsh
# ------------------------------------------------------------
# This closes the Gmsh API session.

gmsh.finalize()