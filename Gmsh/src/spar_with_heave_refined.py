#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu May 28 19:19:24 2026

@author: troy
"""

import gmsh
import math

# ------------------------------------------------------------
# 1. Initialize Gmsh
# ------------------------------------------------------------
# This starts the Gmsh Python API. It must be called before using
# any Gmsh functions.
gmsh.initialize()

# Create a new model and give it a descriptive name.
gmsh.model.add("spar_buoy_with_heave_plate_refined")

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
# 6. Identify reference curves for local refinement
# ------------------------------------------------------------
# To define a local mesh refinement region, we first identify the
# outer circular curves of the heave plate. These curves will be
# used as the reference geometry for a distance-based mesh field.

tol = 1e-6
outer_edge_curves = []

for dim, tag in gmsh.model.getEntities(1):

    # Get the bounding box of the curve.
    xmin, ymin, zmin, xmax, ymax, zmax = gmsh.model.getBoundingBox(dim, tag)

    # Compute the bounding-box dimensions.
    dz = zmax - zmin
    dx = xmax - xmin
    dy = ymax - ymin

    # The outer heave-plate curves lie in horizontal planes.
    is_horizontal_curve = dz < tol

    # The outer circular curves span the heave-plate diameter.
    is_outer_radius = (
        abs(dx - 2 * heave_radius) < 1e-4 or
        abs(dy - 2 * heave_radius) < 1e-4
    )

    # The relevant curves are located at the bottom and top
    # elevations of the heave plate.
    is_at_heave_top_or_bottom = (
        abs(zmin - heave_z0) < 1e-4 or
        abs(zmin - (heave_z0 + heave_height)) < 1e-4
    )

    # Store the curve tag if all geometric criteria are satisfied.
    if is_horizontal_curve and is_outer_radius and is_at_heave_top_or_bottom:
        outer_edge_curves.append(tag)

# ------------------------------------------------------------
# 7. Local mesh refinement
# ------------------------------------------------------------
# We use a background mesh field to refine the mesh near the outer
# heave-plate edge while allowing the mesh to become coarser away
# from that region.

# 7a) Define mesh sizes
# Use approximately 5 elements through the heave-plate thickness.
mesh_size = 0.02
heave_mesh_size = heave_height / 5

# 7b) Distance field
# The Distance field computes distance from selected geometric
# entities. Here, distance is measured from the outer heave-plate
# curves identified above.
distance_field = gmsh.model.mesh.field.add("Distance")

# For curved entities, Gmsh approximates the distance calculation
# using sampled points along the curve. We choose a sampling value
# based on the desired fine mesh size around the heave-plate perimeter.
N_pts = math.ceil((2 * heave_radius * math.pi) / heave_mesh_size)
gmsh.model.mesh.field.setNumber(distance_field, "Sampling", N_pts)
gmsh.model.mesh.field.setNumbers(distance_field, "CurvesList", outer_edge_curves)

# 7c) Threshold field
# The Threshold field converts distance into a target mesh size.
# Points close to the selected curves use SizeMin, points far from
# the curves use SizeMax, and points between DistMin and DistMax
# transition gradually between those values.
threshold_field = gmsh.model.mesh.field.add("Threshold")

gmsh.model.mesh.field.setNumber(threshold_field, "InField", distance_field)
gmsh.model.mesh.field.setNumber(threshold_field, "SizeMin", heave_mesh_size)
gmsh.model.mesh.field.setNumber(threshold_field, "SizeMax", mesh_size)
gmsh.model.mesh.field.setNumber(threshold_field, "DistMin", heave_height)
gmsh.model.mesh.field.setNumber(threshold_field, "DistMax", 5 * heave_height)

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
gmsh.model.mesh.field.setAsBackgroundMesh(threshold_field)

# ------------------------------------------------------------
# 8. Generate the mesh
# ------------------------------------------------------------
# Capytaine uses a Boundary Element Method, so we only need the
# body surface mesh rather than a full 3D volume mesh.

gmsh.model.mesh.generate(2)

# ------------------------------------------------------------
# 9. Write the mesh to a file
# ------------------------------------------------------------
# The .msh format is Gmsh's native mesh format.

gmsh.write("spar_buoy_with_heave_plate_refined.msh")

# ------------------------------------------------------------
# 10. Finalize Gmsh
# ------------------------------------------------------------
# This closes the Gmsh API session.

gmsh.finalize()