#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sat Jul 25 20:19:08 2026

@author: troy
"""

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
gmsh.model.add("spar_buoy_refined")

# ------------------------------------------------------------
# 2. Define cylinder parameters
# ------------------------------------------------------------
# For this first example, we define a simple vertical cylinder
# representing a spar. All dimensions are specified in meters.
#
# The cylinder axis will point in the positive z-direction.

spar_radius = 0.0254     # Cylinder radius [m] 
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

# Create the circular bottom surface of the spar. Since the two
# radii are equal, addDisk creates a circle rather than an ellipse.
bottom_disk = gmsh.model.occ.addDisk(
    spar_x0,
    spar_y0,
    spar_z0,
    spar_radius,
    spar_radius
)

# Specify the number of mesh layers along the spar axis. This
# controls the axial resolution independently of the resolution
# around the circumference.
n_axial = 80

# Extrude the bottom disk along the cylinder axis. The extrusion
# creates the cylindrical volume, the top face, and the lateral
# surface. numElements prescribes the number of axial mesh layers.
#
# recombine=True forms quadrilateral panels on the cylindrical wall
# instead of splitting each panel into two triangles.
extruded_entities = gmsh.model.occ.extrude(
    [(2, bottom_disk)],
    spar_dx,
    spar_dy,
    spar_dz,
    numElements=[n_axial],
    recombine=True
)


# ------------------------------------------------------------
# 4. Synchronize the geometry
# ------------------------------------------------------------
# After creating geometry with the OpenCASCADE kernel, we must
# synchronize it with the main Gmsh model before meshing.

gmsh.model.occ.synchronize()

# ------------------------------------------------------------
# 5. Set the circumferential resolution
# ------------------------------------------------------------
# Specify the number of mesh elements around the circular edge.
# This controls how accurately the mesh represents the cylinder's
# circular cross-section.
n_circumference = 24

# Obtain the one-dimensional curves that form the boundary of the
# bottom disk. For a simple disk, this is the outer circular curve.
bottom_boundary = gmsh.model.getBoundary(
    [(2, bottom_disk)],
    oriented=False,
    recursive=False
)

# Extract the tags of the one-dimensional boundary entities.
bottom_curves = []

for dimension, tag in bottom_boundary:
    if dimension == 1:
        bottom_curves.append(tag)

# A transfinite curve constraint is specified using the number of
# nodes rather than the number of elements. Therefore, 24 elements
# require 25 nodes.
for curve in bottom_curves:
    gmsh.model.mesh.setTransfiniteCurve(
        curve,
        n_circumference + 1
    )


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

gmsh.write("../meshes/new_spar_buoy_refined.msh")

# ------------------------------------------------------------
# 8. Finalize Gmsh
# ------------------------------------------------------------
# This closes the Gmsh API session.

gmsh.finalize()