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
            #abs(zmin - z0) < 1e-4
            abs(zmin - z0) < 1e-4 or
            abs(zmin - (z0 + height)) < 1e-4
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

def get_new_edge_curves(gmsh, radius, z_levels):
    """
    Return horizontal circular curve tags at selected z elevations.

    Parameters
    ----------
    gmsh
        Imported Gmsh module.
    radius : float
        Expected radius of the circular curves.
    z_levels : list[float]
        Elevations at which the circular curves should be located.

    Returns
    -------
    list[int]
        Tags of matching one-dimensional curve entities.
    """

    geometry_tol = 1e-6
    size_tol = 1e-4
    z_tol = 1e-4

    edge_curves = []

    for dim, tag in gmsh.model.getEntities(1):

        xmin, ymin, zmin, xmax, ymax, zmax = (
            gmsh.model.getBoundingBox(dim, tag)
        )

        dx = xmax - xmin
        dy = ymax - ymin
        dz = zmax - zmin

        # The curve must lie in a horizontal plane.
        is_horizontal = dz < geometry_tol

        # A circular curve of the requested radius spans one diameter
        # in both the x- and y-directions.
        matches_radius = (
            abs(dx - 2.0 * radius) < size_tol
            and abs(dy - 2.0 * radius) < size_tol
        )

        # Since the curve is horizontal, zmin and zmax are effectively
        # the same. Match that elevation against any requested level.
        matches_z_level = False
        
        for z_level in z_levels:
            if abs(zmin - z_level) < z_tol:
                matches_z_level = True
                break

        if is_horizontal and matches_radius and matches_z_level:
            edge_curves.append(tag)

    return edge_curves


def get_split_cylindrical_surfaces(gmsh, radius, z_levels):
    """
    Find the two half-cylinder surfaces created by splitting a vertical
    cylindrical wall through its axis.
    """

    tol = 1e-4

    target_zmin = min(z_levels)
    target_zmax = max(z_levels)

    matching_surfaces = []

    for dim, tag in gmsh.model.getEntities(2):

        xmin, ymin, zmin, xmax, ymax, zmax = (
            gmsh.model.getBoundingBox(dim, tag)
        )

        dx = xmax - xmin
        dy = ymax - ymin
        dz = zmax - zmin

        matches_height = (
            abs(zmin - target_zmin) < tol
            and abs(zmax - target_zmax) < tol
        )

        # A half-cylinder produced by the x = 0 splitting plane spans:
        #   radius in x
        #   diameter in y
        matches_half_cylinder = (
            abs(dx - radius) < tol
            and abs(dy - 2.0 * radius) < tol
        )

        if matches_height and matches_half_cylinder:
            matching_surfaces.append(tag)

    return matching_surfaces
