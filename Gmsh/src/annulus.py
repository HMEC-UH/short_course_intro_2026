#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Generate a closed surface mesh for an annular body surrounding a spar.

The annulus is created using the same extrusion-based approach used for
the heave plate:

1. Create an outer disk.
2. Subtract an inner disk to form an annular source surface.
3. Extrude the annular surface through the body thickness.
4. Export only the exterior surface mesh.

The annulus is a separate hydrodynamic body and should not share nodes
or panels with the spar.
"""

import gmsh


# =============================================================================
# USER-DEFINED PARAMETERS
# =============================================================================

# Existing spar geometry -------------------------------------------------------

spar_radius = 0.0254


# Annulus geometry -------------------------------------------------------------

# Water-filled radial gap between the spar and annulus.
radial_clearance = 0.0025

annulus_inner_radius = (
    spar_radius + radial_clearance
)

annulus_outer_radius = 0.1524
annulus_height = 0.0508

# Bottom elevation of the annulus in its equilibrium position.
annulus_z_bottom = 2.0

annulus_z_top = (
    annulus_z_bottom + annulus_height
)


# Mesh resolution --------------------------------------------------------------

# Number of panels through the vertical height of the annulus.
n_annulus_vertical = 4

# Approximate mesh size on the annulus top and bottom faces.
annulus_mesh_size = 0.015


# =============================================================================
# INITIALIZE GMSH
# =============================================================================

if gmsh.isInitialized():
    gmsh.finalize()

gmsh.initialize()

try:
    gmsh.model.add("annular_body")

    # -------------------------------------------------------------------------
    # 1. Create the annular source surface
    # -------------------------------------------------------------------------

    # The outer disk defines the complete annulus footprint.
    outer_disk = gmsh.model.occ.addDisk(
        0.0,
        0.0,
        annulus_z_bottom,
        annulus_outer_radius,
        annulus_outer_radius,
    )

    # The inner disk defines the opening around the spar.
    #
    # Its radius is slightly larger than the spar radius so that a finite
    # water-filled clearance remains between the two bodies.
    inner_disk = gmsh.model.occ.addDisk(
        0.0,
        0.0,
        annulus_z_bottom,
        annulus_inner_radius,
        annulus_inner_radius,
    )

    # Subtract the inner disk from the outer disk.
    #
    # Unlike the heave-plate example, the central disk is not needed here,
    # so a Boolean cut is simpler than retaining both partitioned regions.
    annular_entities, _ = gmsh.model.occ.cut(
        [(2, outer_disk)],
        [(2, inner_disk)],
        removeObject=True,
        removeTool=True,
    )

    gmsh.model.occ.synchronize()

    annular_source_surfaces = [
        tag
        for dimension, tag in annular_entities
        if dimension == 2
    ]

    if len(annular_source_surfaces) != 1:
        raise RuntimeError(
            "Expected one annular source surface, "
            f"but found {annular_source_surfaces}."
        )

    annular_source_surface = (
        annular_source_surfaces[0]
    )

    print(
        "Annular source surface:",
        annular_source_surface,
    )

    # -------------------------------------------------------------------------
    # 2. Extrude the annular surface
    # -------------------------------------------------------------------------

    # Extruding the source surface creates:
    #
    #   - the annulus bottom face;
    #   - the annulus top face;
    #   - the outer cylindrical wall;
    #   - the inner cylindrical wall facing the spar.
    #
    # numElements controls the vertical resolution of both cylindrical walls.
    # recombine=True creates quadrilateral panels on those extruded walls.
    extrusion_entities = gmsh.model.occ.extrude(
        [(2, annular_source_surface)],
        0.0,
        0.0,
        annulus_height,
        numElements=[n_annulus_vertical],
        recombine=True,
    )

    gmsh.model.occ.synchronize()

    # -------------------------------------------------------------------------
    # 3. Identify the exterior surface of the annulus volume
    # -------------------------------------------------------------------------

    volume_entities = gmsh.model.getEntities(3)

    if len(volume_entities) != 1:
        raise RuntimeError(
            "Expected one annulus volume, "
            f"but found {volume_entities}."
        )

    boundary_entities = gmsh.model.getBoundary(
        volume_entities,
        combined=True,
        oriented=False,
        recursive=False,
    )

    exterior_surfaces = sorted(
        tag
        for dimension, tag in boundary_entities
        if dimension == 2
    )

    print("Annulus volume:", volume_entities)
    print("Exterior surfaces:", exterior_surfaces)

    # The exterior surfaces should include the top, bottom, inner wall,
    # and outer wall of the annulus.
    if len(exterior_surfaces) != 4:
        print(
            "Warning: Expected four exterior surfaces "
            "for a simple annulus."
        )

    # -------------------------------------------------------------------------
    # 4. Mark the annulus surface for export
    # -------------------------------------------------------------------------

    annulus_group = gmsh.model.addPhysicalGroup(
        2,
        exterior_surfaces,
    )

    gmsh.model.setPhysicalName(
        2,
        annulus_group,
        "Annulus wetted surface",
    )

    # -------------------------------------------------------------------------
    # 5. Set the unstructured face resolution
    # -------------------------------------------------------------------------

    # The top and bottom annular faces are triangulated automatically.
    # This target size controls their approximate panel dimensions.
    gmsh.model.mesh.setSize(
        gmsh.model.getEntities(0),
        annulus_mesh_size,
    )

    gmsh.option.setNumber(
        "Mesh.MeshSizeMax",
        annulus_mesh_size,
    )

    # -------------------------------------------------------------------------
    # 6. Generate and export the surface mesh
    # -------------------------------------------------------------------------

    gmsh.model.mesh.generate(2)

    gmsh.model.mesh.removeDuplicateNodes()

    # Export only surfaces belonging to the physical group.
    gmsh.option.setNumber(
        "Mesh.SaveAll",
        0,
    )

    gmsh.write(
        "../meshes/annular_body.msh"
    )

    # -------------------------------------------------------------------------
    # 7. Report the surface element counts
    # -------------------------------------------------------------------------

    element_types, element_tags, _ = (
        gmsh.model.mesh.getElements(dim=2)
    )

    print("\nSurface elements:")

    for element_type, tags in zip(
        element_types,
        element_tags,
    ):
        element_name = (
            gmsh.model.mesh.getElementProperties(
                element_type
            )[0]
        )

        print(
            f"  {element_name}: {len(tags)}"
        )

finally:
    gmsh.finalize()