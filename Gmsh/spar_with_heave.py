#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu May 28 15:12:53 2026

@author: troy
"""

import gmsh

# ------------------------------------------------------------
# 1. Initialize Gmsh
# ------------------------------------------------------------
# This starts the Gmsh Python API. It must be called before using
# any Gmsh functions.
gmsh.initialize()

# Create a new model and give it a descriptive name.
gmsh.model.add("spar_buoy_with_heave_plate")

# ------------------------------------------------------------
# 2. Define cylinder parameters
# ------------------------------------------------------------
# All dimensions are specified in meters. Gmsh itself is unitless,
# but Capytaine expects SI units, so we will use meters throughout.

# Spar buoy dimensions
spar_radius = 0.165       # [m] approximately 6.5 in
spar_height = 6.096       # [m] approximately 20 ft

# Heave plate dimensions
heave_radius = 1.2192     # [m] approximately 4 ft
heave_height = 0.0254     # [m] approximately 1 in

# Spar location and orientation
# The spar begins at z = 0 and extends upward in the +z direction.
spar_x0 = 0.0
spar_y0 = 0.0
spar_z0 = 0.0

spar_dx = 0.0
spar_dy = 0.0
spar_dz = spar_height

# Heave plate location and orientation
# The heave plate is also modeled as a short cylinder. In this
# example, it is placed at the bottom of the spar.
heave_x0 = 0.0
heave_y0 = 0.0
heave_z0 = 0.0

heave_dx = 0.0
heave_dy = 0.0
heave_dz = heave_height

# ------------------------------------------------------------
# 3. Create geometric primitives
# ------------------------------------------------------------
# We use the OpenCASCADE geometry kernel through gmsh.model.occ.
# The addCylinder function creates a cylinder primitive from:
#   - the center of the first circular face,
#   - an axis vector,
#   - and a radius.
#
# Each call returns an integer tag identifying the new volume.

spar_buoy = gmsh.model.occ.addCylinder(
    spar_x0, spar_y0, spar_z0,
    spar_dx, spar_dy, spar_dz,
    spar_radius
)

heave_plate = gmsh.model.occ.addCylinder(
    heave_x0, heave_y0, heave_z0,
    heave_dx, heave_dy, heave_dz,
    heave_radius
)

# ------------------------------------------------------------
# 4. Combine primitives using a Boolean union
# ------------------------------------------------------------
# The spar and heave plate were created as two separate volumes.
# To mesh them as one continuous body, we combine them using a
# Boolean union operation.
#
# Gmsh refers to volume entities using dimension-tag pairs:
#   (3, spar_buoy)    -> 3D volume associated with the spar
#   (3, heave_plate)  -> 3D volume associated with the heave plate
#
# The fuse operation returns the resulting combined geometry.

combined_body, _ = gmsh.model.occ.fuse(
    [(3, spar_buoy)],
    [(3, heave_plate)]
)

# ------------------------------------------------------------
# 5. Synchronize the geometry
# ------------------------------------------------------------
# After creating and modifying geometry with OpenCASCADE, we must
# synchronize the geometry kernel with the main Gmsh model before
# generating the mesh.

gmsh.model.occ.synchronize()

# ------------------------------------------------------------
# 6. Set mesh size
# ------------------------------------------------------------
# This controls the approximate size of mesh elements.
# Smaller values create a finer mesh; larger values create
# a coarser mesh.

mesh_size = 0.02

gmsh.option.setNumber("Mesh.CharacteristicLengthMin", mesh_size)
gmsh.option.setNumber("Mesh.CharacteristicLengthMax", mesh_size)

# ------------------------------------------------------------
# 7. Generate the mesh
# ------------------------------------------------------------
# Capytaine uses a Boundary Element Method, so we only need the
# body surface mesh rather than a full 3D volume mesh.

gmsh.model.mesh.generate(2)

# ------------------------------------------------------------
# 8. Write the mesh to a file
# ------------------------------------------------------------
# The .msh format is Gmsh's native mesh format.

gmsh.write("spar_buoy_with_heave_plate.msh")

# ------------------------------------------------------------
# 9. Finalize Gmsh
# ------------------------------------------------------------
# This closes the Gmsh API session.

gmsh.finalize()