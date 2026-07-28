#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Generate a surface mesh for a vertical spar with a circular heave plate.

The geometry is constructed using staged extrusion:

1. Partition the heave-plate footprint into:
   - a central disk with the spar radius;
   - a surrounding annulus.

2. Extrude both regions through the heave-plate thickness.

3. Continue extruding the central top surface to create the spar.

This approach preserves the structured extrusion mesh on the spar while
producing an unstructured triangular mesh on the heave-plate faces.

Only the exterior surfaces are exported. Internal construction surfaces
between the three volumes are excluded from the final mesh.
"""

import math

import gmsh


# =============================================================================
# USER-DEFINED PARAMETERS
# =============================================================================

# Geometry --------------------------------------------------------------------

spar_radius = 0.0254          # Spar radius [m]
spar_height = 6.096           # Spar height above the plate [m]

plate_radius = 0.3048         # Heave-plate radius [m]
plate_thickness = 0.009525    # Heave-plate thickness [m]

# The top of the heave plate is placed at z = 0.
plate_z_top = 0.0
plate_z_bottom = plate_z_top - plate_thickness


# Mesh resolution -------------------------------------------------------------

# Number of panels around the spar circumference.
n_spar_circumference = 24

# Number of panels along the spar height.
n_spar_axial = 80

# Number of panels through the heave-plate thickness.
n_plate_thickness = 2

# Approximate element size on the unstructured heave-plate faces [m].
plate_mesh_size = 0.05


# Numerical tolerances --------------------------------------------------------

geometry_tolerance = 1.0e-6
curve_length_tolerance = 1.0e-6
surface_area_tolerance_fraction = 0.01


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def find_source_circles(
    source_surfaces,
    spar_radius,
    plate_radius,
    source_z,
):
    """
    Identify the inner and outer circular curves of the partitioned plate.

    The inner circle is shared by the central disk and annulus. Its mesh
    discretization controls the number of panels around the spar.

    Parameters
    ----------
    source_surfaces : list[int]
        Tags of the partitioned source surfaces.
    spar_radius : float
        Radius of the spar.
    plate_radius : float
        Radius of the heave plate.
    source_z : float
        Vertical position of the source surfaces.

    Returns
    -------
    inner_circle : int
        Curve tag at the spar radius.
    outer_circle : int
        Curve tag at the plate radius.
    """

    expected_inner_length = 2.0 * math.pi * spar_radius
    expected_outer_length = 2.0 * math.pi * plate_radius

    source_boundary = gmsh.model.getBoundary(
        [(2, surface) for surface in source_surfaces],
        combined=False,
        oriented=False,
        recursive=False,
    )

    # A curve can belong to more than one source surface. Converting the
    # returned tags to a set removes duplicate entries.
    source_curves = sorted({
        tag
        for dimension, tag in source_boundary
        if dimension == 1
    })

    inner_circles = []
    outer_circles = []

    for curve in source_curves:

        _, _, z_min, _, _, z_max = gmsh.model.getBoundingBox(
            1,
            curve,
        )

        curve_length = gmsh.model.occ.getMass(
            1,
            curve,
        )

        lies_on_source_plane = (
            abs(z_min - source_z) < geometry_tolerance
            and abs(z_max - source_z) < geometry_tolerance
        )

        if not lies_on_source_plane:
            continue

        if (
            abs(curve_length - expected_inner_length)
            < curve_length_tolerance
        ):
            inner_circles.append(curve)

        elif (
            abs(curve_length - expected_outer_length)
            < curve_length_tolerance
        ):
            outer_circles.append(curve)

    if len(inner_circles) != 1:
        raise RuntimeError(
            "Expected one circular source curve at the spar radius, "
            f"but found {inner_circles}."
        )

    if len(outer_circles) != 1:
        raise RuntimeError(
            "Expected one circular source curve at the plate radius, "
            f"but found {outer_circles}."
        )

    return inner_circles[0], outer_circles[0]


def find_central_horizontal_surface(
    target_z,
    target_radius,
):
    """
    Find the horizontal circular surface at a specified elevation.

    This is used to identify the central top surface of the plate before
    it is extruded upward to create the spar.
    """

    expected_area = math.pi * target_radius**2
    area_tolerance = (
        surface_area_tolerance_fraction * expected_area
    )

    matching_surfaces = []

    for dimension, surface in gmsh.model.getEntities(2):

        _, _, z_min, _, _, z_max = gmsh.model.getBoundingBox(
            dimension,
            surface,
        )

        surface_area = gmsh.model.occ.getMass(
            dimension,
            surface,
        )

        is_horizontal = (
            abs(z_max - z_min) < geometry_tolerance
        )

        lies_at_target_z = (
            abs(z_min - target_z) < geometry_tolerance
            and abs(z_max - target_z) < geometry_tolerance
        )

        matches_expected_area = (
            abs(surface_area - expected_area) < area_tolerance
        )

        if (
            is_horizontal
            and lies_at_target_z
            and matches_expected_area
        ):
            matching_surfaces.append(surface)

    if len(matching_surfaces) != 1:
        raise RuntimeError(
            "Expected one central horizontal surface at "
            f"z = {target_z}, but found {matching_surfaces}."
        )

    return matching_surfaces[0]


def get_exterior_surfaces():
    """
    Return the exterior surfaces of the complete volume assembly.

    The model contains three construction volumes:

    - the annular part of the heave plate;
    - the central plug within the heave plate;
    - the spar.

    When the boundaries of all volumes are evaluated together, shared
    internal surfaces cancel. The remaining surfaces form the exterior
    boundary required for the hydrodynamic mesh.
    """

    volumes = gmsh.model.getEntities(3)

    if not volumes:
        raise RuntimeError(
            "No three-dimensional construction volumes were found."
        )

    combined_boundary = gmsh.model.getBoundary(
        volumes,
        combined=True,
        oriented=False,
        recursive=False,
    )

    exterior_surfaces = sorted(
        tag
        for dimension, tag in combined_boundary
        if dimension == 2
    )

    if not exterior_surfaces:
        raise RuntimeError(
            "No exterior surfaces were identified."
        )

    return volumes, exterior_surfaces


def report_surface_elements(surface_tags):
    """
    Report the number of exterior triangular and quadrilateral elements.
    """

    element_counts = {}

    for surface in surface_tags:

        element_types, element_tags, _ = (
            gmsh.model.mesh.getElements(
                dim=2,
                tag=surface,
            )
        )

        for element_type, tags in zip(
            element_types,
            element_tags,
        ):
            element_name = (
                gmsh.model.mesh.getElementProperties(
                    element_type
                )[0]
            )

            element_counts[element_name] = (
                element_counts.get(element_name, 0)
                + len(tags)
            )

    print("\nExterior surface elements:")

    total_elements = 0

    for element_name, count in sorted(
        element_counts.items()
    ):
        print(f"  {element_name}: {count}")
        total_elements += count

    print(f"  Total: {total_elements}")


# =============================================================================
# BUILD THE MODEL
# =============================================================================

# Finalize any Gmsh session left open by an earlier interactive run.
if gmsh.isInitialized():
    gmsh.finalize()

gmsh.initialize()

try:
    gmsh.model.add("spar_with_heave_plate")

    # -------------------------------------------------------------------------
    # 1. Partition the heave-plate footprint
    # -------------------------------------------------------------------------

    # The large disk represents the complete plate footprint.
    outer_disk = gmsh.model.occ.addDisk(
        0.0,
        0.0,
        plate_z_bottom,
        plate_radius,
        plate_radius,
    )

    # The smaller disk matches the spar cross section.
    inner_disk = gmsh.model.occ.addDisk(
        0.0,
        0.0,
        plate_z_bottom,
        spar_radius,
        spar_radius,
    )

    # Fragmenting the disks divides the plate footprint into two conformal
    # regions:
    #
    #   1. a central disk beneath the spar;
    #   2. an annulus forming the remainder of the heave plate.
    #
    # The fragment operation is performed before extrusion so that the
    # resulting volumes share geometric interfaces and mesh nodes.
    partitioned_entities, _ = gmsh.model.occ.fragment(
        [(2, outer_disk)],
        [(2, inner_disk)],
    )

    gmsh.model.occ.synchronize()

    source_surfaces = sorted(
        tag
        for dimension, tag in partitioned_entities
        if dimension == 2
    )

    if len(source_surfaces) != 2:
        raise RuntimeError(
            "Expected the footprint to contain one central disk and "
            f"one annulus, but found surfaces {source_surfaces}."
        )

    print("Partitioned source surfaces:", source_surfaces)

    # -------------------------------------------------------------------------
    # 2. Control the spar circumferential resolution
    # -------------------------------------------------------------------------

    inner_source_circle, outer_source_circle = (
        find_source_circles(
            source_surfaces=source_surfaces,
            spar_radius=spar_radius,
            plate_radius=plate_radius,
            source_z=plate_z_bottom,
        )
    )

    print("Spar source circle:", inner_source_circle)
    print("Plate outer circle:", outer_source_circle)

    # A transfinite curve specifies the exact number of nodes on a curve.
    # Therefore, one is added to convert the desired number of panels into
    # the required number of nodes.
    #
    # This circular discretization is inherited by the extruded spar wall.
    gmsh.model.mesh.setTransfiniteCurve(
        inner_source_circle,
        n_spar_circumference + 1,
    )

    # The outer plate circle is intentionally left unconstrained. Its
    # discretization is determined by plate_mesh_size together with the
    # unstructured mesh on the plate faces.

    # -------------------------------------------------------------------------
    # 3. Extrude the complete heave plate
    # -------------------------------------------------------------------------

    gmsh.model.occ.extrude(
        [(2, surface) for surface in source_surfaces],
        0.0,
        0.0,
        plate_thickness,
        numElements=[n_plate_thickness],
        recombine=True,
    )

    gmsh.model.occ.synchronize()

    # -------------------------------------------------------------------------
    # 4. Identify the central top surface of the plate
    # -------------------------------------------------------------------------

    central_top_surface = find_central_horizontal_surface(
        target_z=plate_z_top,
        target_radius=spar_radius,
    )

    print("Central plate-top surface:", central_top_surface)

    # -------------------------------------------------------------------------
    # 5. Continue the central surface upward to create the spar
    # -------------------------------------------------------------------------

    gmsh.model.occ.extrude(
        [(2, central_top_surface)],
        0.0,
        0.0,
        spar_height,
        numElements=[n_spar_axial],
        recombine=True,
    )

    gmsh.model.occ.synchronize()

    # -------------------------------------------------------------------------
    # 6. Extract the exterior boundary
    # -------------------------------------------------------------------------

    volumes, exterior_surfaces = get_exterior_surfaces()

    all_surfaces = {
        tag
        for dimension, tag in gmsh.model.getEntities(2)
    }

    internal_surfaces = sorted(
        all_surfaces - set(exterior_surfaces)
    )

    print("Construction volumes:", volumes)
    print("Exterior surfaces:", exterior_surfaces)
    print("Internal construction surfaces:", internal_surfaces)

    # The model contains multiple construction volumes, but Capytaine needs
    # only their combined exterior boundary. A two-dimensional physical group
    # identifies the surfaces that will be exported.
    wetted_surface_group = gmsh.model.addPhysicalGroup(
        2,
        exterior_surfaces,
    )

    gmsh.model.setPhysicalName(
        2,
        wetted_surface_group,
        "Wetted surface",
    )

    # -------------------------------------------------------------------------
    # 7. Set the unstructured plate-face resolution
    # -------------------------------------------------------------------------

    # Point-based mesh sizes guide the unstructured triangulation on the
    # horizontal plate faces. The transfinite constraint on the inner circle
    # still controls the exact spar circumference.
    gmsh.model.mesh.setSize(
        gmsh.model.getEntities(0),
        plate_mesh_size,
    )

    # MeshSizeMax also limits element growth away from the plate boundaries.
    gmsh.option.setNumber(
        "Mesh.MeshSizeMax",
        plate_mesh_size,
    )

    # -------------------------------------------------------------------------
    # 8. Generate and export the surface mesh
    # -------------------------------------------------------------------------

    gmsh.model.mesh.generate(2)

    # This should normally have little or nothing to remove because the
    # staged construction creates conformal interfaces. It provides an
    # additional safeguard against coincident duplicate nodes.
    gmsh.model.mesh.removeDuplicateNodes()

    report_surface_elements(exterior_surfaces)

    # Mesh.SaveAll = 0 tells Gmsh to write only entities belonging to a
    # physical group. Internal construction surfaces are therefore omitted.
    gmsh.option.setNumber(
        "Mesh.SaveAll",
        0,
    )

    gmsh.write("../meshes/staged_extrusion_spar_plate.msh")


finally:
    gmsh.finalize()