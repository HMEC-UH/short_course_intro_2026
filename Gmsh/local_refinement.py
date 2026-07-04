#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Jun 29 09:57:59 2026

@author: troy
"""

import math

def get_edge_curves(gmsh, radius, z0, height):
    
    tol = 1e-6
    outer_edge_curves = []

    for dim, tag in gmsh.model.getEntities(1):

        # Get the bounding box of the curve.
        xmin, ymin, zmin, xmax, ymax, zmax = gmsh.model.getBoundingBox(dim, tag)

        # Compute the bounding-box dimensions.
        dz = zmax - zmin
        dx = xmax - xmin
        dy = ymax - ymin

        # The curves lie in horizontal planes.
        is_horizontal_curve = dz < tol

        # The circular curves span the diameter.
        is_outer_radius = (
            abs(dx - 2 * radius) < 1e-4 or
            abs(dy - 2 * radius) < 1e-4
        )

        # The relevant curves are located at the bottom and top
        # elevations of the cylinder.
        is_at_heave_top_or_bottom = (
            abs(zmin - z0) < 1e-4
            # abs(zmin - z0) < 1e-4 or
            # abs(zmin - (z0 + height)) < 1e-4
        )

        # Store the curve tag if all geometric criteria are satisfied.
        if is_horizontal_curve and is_outer_radius and is_at_heave_top_or_bottom:
            outer_edge_curves.append(tag)
            
    return outer_edge_curves

def get_threshold_field(gmsh, edge_curves, radius,
                        size_min, size_max,
                        dist_min, dist_max):
    
    # 7a) Distance field
    # The Distance field computes distance from selected geometric
    # entities. Here, distance is measured from the outer heave-plate
    # curves identified above.
    distance_field = gmsh.model.mesh.field.add("Distance")
    
    # For curved entities, Gmsh approximates the distance calculation
    # using sampled points along the curve. We choose a sampling value
    # based on the desired fine mesh size around the heave-plate perimeter.
    N_pts = math.ceil((2 * radius * math.pi) / size_min)
    gmsh.model.mesh.field.setNumber(distance_field, "Sampling", N_pts)
    gmsh.model.mesh.field.setNumbers(distance_field, "CurvesList", edge_curves)
    
    # 7b) Threshold field
    # The Threshold field converts distance into a target mesh size.
    # Points close to the selected curves use SizeMin, points far from
    # the curves use SizeMax, and points between DistMin and DistMax
    # transition gradually between those values.
    threshold_field = gmsh.model.mesh.field.add("Threshold")
    
    gmsh.model.mesh.field.setNumber(threshold_field, "InField", distance_field)
    gmsh.model.mesh.field.setNumber(threshold_field, "SizeMin", size_min)
    gmsh.model.mesh.field.setNumber(threshold_field, "SizeMax", size_max)
    gmsh.model.mesh.field.setNumber(threshold_field, "DistMin", dist_min)
    gmsh.model.mesh.field.setNumber(threshold_field, "DistMax", dist_max)
    
    return threshold_field