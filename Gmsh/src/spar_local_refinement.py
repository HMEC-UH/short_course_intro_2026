#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu May 28 10:09:44 2026

@author: troy
"""

import gmsh
from local_refinement import get_edge_curves, get_threshold_field

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
# 5. Identify reference curves for local refinement
# ------------------------------------------------------------
# To define a local mesh refinement region, we first identify the
# outer circular curves of the heave plate. These curves will be
# used as the reference geometry for a distance-based mesh field.

spar_edge_curves = get_edge_curves(gmsh, spar_radius, 0, spar_height-0)

print("Spar curves:", spar_edge_curves)


# ------------------------------------------------------------
# 7. Local mesh refinement
# ------------------------------------------------------------
# We use a background mesh field to refine the mesh near the outer
# heave-plate edge while allowing the mesh to become coarser away
# from that region.
mesh_size = 0.05

spar_threshold = get_threshold_field(
    gmsh,
    spar_edge_curves,
    spar_radius,
    size_min=spar_radius/5,
    size_max=mesh_size,
    dist_min=spar_radius/10,
    dist_max=10*spar_radius
)
   
# 7d) Mesh generation options
# Prevent Gmsh from extending small boundary mesh sizes across entire
# adjacent surfaces. This helps keep refinement localized near the
# heave-plate edge instead of spreading across the full top and bottom
# faces of the plate.
gmsh.option.setNumber("Mesh.MeshSizeExtendFromBoundary", 0)

# Optional advanced controls:
# These can be disabled if you want the background field to dominate
# the mesh-size calculation without additional point- or curvature-based
# refinement.
#
# gmsh.option.setNumber("Mesh.MeshSizeFromPoints", 0)
# gmsh.option.setNumber("Mesh.MeshSizeFromCurvature", 0)

# 7e) Activate the background mesh field
# The threshold field now defines the target mesh size throughout
# the model.
gmsh.model.mesh.field.setAsBackgroundMesh(spar_threshold)

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

gmsh.write("../meshes/spar_buoy_refined.msh")

# ------------------------------------------------------------
# 8. Finalize Gmsh
# ------------------------------------------------------------
# This closes the Gmsh API session.

gmsh.finalize()