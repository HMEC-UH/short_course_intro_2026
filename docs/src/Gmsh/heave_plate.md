In the previous section, we created a simple cylindrical spar by extruding a circular surface. We will now extend that approach by adding a **heave plate** to the bottom of the spar.

The final geometry consists of two familiar shapes: a long cylindrical spar and a thin circular plate. However, simply creating two overlapping cylinders is not ideal for the meshing strategy we want to use. Instead, we will construct the geometry in stages so that the spar and heave plate share conformal interfaces while retaining independent control over their mesh resolution.

The basic construction sequence is:

1. divide the heave-plate footprint into a central disk and surrounding annulus;
2. extrude both surfaces through the heave-plate thickness;
3. identify the central surface on top of the plate;
4. extrude that surface upward to create the spar;
5. identify the exterior boundary of the completed assembly;
6. apply the desired mesh resolution;
7. generate and export the surface mesh.

The complete script also includes several **helper functions** that identify geometric entities based on their physical properties rather than relying on Gmsh entity numbers. We will discuss these separately before stepping through the main construction workflow.

---

## 1. User-Defined Parameters

As before, we begin by collecting the principal geometry, mesh, tolerance, and output parameters near the top of the script.

```python
# =============================================================================
# 1. USER-DEFINED PARAMETERS
# =============================================================================

# Spar geometry ---------------------------------------------------------------
spar_radius = 0.0301625       # Cylinder radius [m] (2.375" dia)
spar_height = 6.096           # Spar height above the plate [m]


# Annulus geometry ------------------------------------------------------------
plate_radius = 0.3048         # Heave-plate radius [m]
plate_thickness = 0.009525    # Heave-plate thickness [m]

# The top of the heave plate is placed at z = 0.
plate_z_top = 0.0

# Annulus coordinates
annulus_x0 = 0.0
annulus_y0 = 0.0
annulus_z0 = 0.0

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

# Names------------------------------------------------------------------------
model_name = 'spar_with_heave_plate'
mesh_fname = 'spar_with_heave_plate'
```

The spar dimensions are unchanged from the previous example: $r_s = 0.0301625~\mathrm{m}$ and $H_s = 6.096~\mathrm{m}$. The heave plate has a much larger radius, $r_p = 0.3048~\mathrm{m}$, but is comparatively thin, $t_p = 0.009525~\mathrm{m}$. The top of the plate is placed at $z=0$, so the plate extends downward from this elevation. 

### Independent Mesh Controls

The mesh is again controlled independently in several directions:

```python
n_spar_circumference = 24
n_spar_axial = 80
n_plate_thickness = 2
plate_mesh_size = 0.05
```

The first two parameters control the spar in the same manner as the previous example.

The new parameter

```python
n_plate_thickness = 2
```

controls the number of layers through the thickness of the heave plate.

The horizontal faces of the plate are treated differently. Instead of prescribing an exact number of elements, we provide an approximate target element size:

```python
plate_mesh_size = 0.05
```

This allows Gmsh to create an **unstructured triangular mesh** across the relatively large horizontal plate surfaces while retaining the structured extrusion mesh used on the spar.

!!! note "Different Mesh Strategies"
    There is no requirement that every surface of a body use the same type of discretization. In this example, we deliberately combine structured quadrilateral regions with unstructured triangular regions so that each part of the geometry can be meshed in a way appropriate to its shape.

The final group contains numerical tolerances used later when identifying curves and surfaces from their geometric properties.

```python
geometry_tolerance = 1.0e-6
curve_length_tolerance = 1.0e-6
surface_area_tolerance_fraction = 0.01
```

These values are not physical dimensions of the body. They are small tolerances used when asking questions such as:

* Is this curve located at the expected elevation?
* Does this curve have the expected circumference?
* Does this surface have approximately the expected area?

---

## Helper Functions

Before initializing Gmsh, the script defines several helper functions:

```python
find_source_circles(...)
find_central_horizontal_surface(...)
get_exterior_surfaces()
report_surface_elements(...)
```

These functions make the main body of the script easier to read, but they also serve an important technical purpose.

Gmsh assigns each point, curve, surface, and volume an integer **tag**. These tags are useful identifiers, but we generally do not want to assume that a particular surface will always be assigned a particular number.

For example, we should avoid writing logic such as:

```python
central_surface = 7
```

and assuming that Surface 7 will always correspond to the top of the central disk.

Instead, the helper functions identify entities using measurable geometric properties such as:

* elevation,
* circumference,
* surface area,
* and whether a surface belongs to the exterior boundary.

This makes the script much more robust.

### Finding the Source Circles

The `find_source_circles()` function identifies the inner and outer circular curves of the partitioned plate footprint.

The expected circumferences are calculated from $C = 2\pi r$.

Therefore,

```python
expected_inner_length = 2.0 * math.pi * spar_radius
expected_outer_length = 2.0 * math.pi * plate_radius
```

represent the expected circumference at the spar radius and plate radius, respectively.

The function then examines the available curves and compares their measured lengths and vertical positions against these expected values.

This allows the script to distinguish between:

* the **inner circle**, which will control the spar circumference; and
* the **outer circle**, which defines the outside edge of the heave plate.

### Finding the Central Horizontal Surface

The `find_central_horizontal_surface()` function performs a similar task for surfaces.

For a circular surface of radius $r$, the expected area is

$$
A=\pi r^2.
$$

The function searches the model for a horizontal surface located at the desired elevation whose area matches the expected area of the spar cross-section.

This allows us to locate the central top surface of the heave plate after extrusion without relying on an entity tag.

### Finding the Exterior Surfaces

The completed model will contain several construction volumes. Some surfaces lie on the outside of the body, while others exist only at the interfaces between adjacent volumes.

The `get_exterior_surfaces()` function determines which surfaces form the actual exterior boundary of the complete body.

This distinction will become especially important when the mesh is exported for Capytaine.

---

## 2. Initialize Gmsh

The initialization process is the same as in the previous example.

```python
# =============================================================================
# 2. INITIALIZE GMSH
# =============================================================================
if gmsh.isInitialized():
    gmsh.finalize()

# This starts the Gmsh Python API. It must be called before using
# any Gmsh functions.
gmsh.initialize()


# Give the model a name. This is useful when working with
# multiple geometries or when inspecting output files.
gmsh.model.add(model_name)
```

---

## 3. Create Geometry

The heave plate is constructed first, beginning at its bottom surface.

```python
# =============================================================================
# 3. CREATE GEOMETRY
# =============================================================================
# Bottom of plate
plate_z_bottom = plate_z_top - plate_thickness
```

Since the top of the plate is defined at $z=0$, the bottom is located at $z_{\mathrm{bottom}} = z_{\mathrm{top}}-t_p$. For the present geometry, $z_{\mathrm{bottom}}= -0.009525~\mathrm{m}$.

### Create Two Circular Surfaces

We then create two disks on this plane:

```python
outer_disk = gmsh.model.occ.addDisk(
    annulus_x0,
    annulus_y0,
    plate_z_bottom,
    plate_radius,
    plate_radius,
)

inner_disk = gmsh.model.occ.addDisk(
    annulus_x0,
    annulus_y0,
    plate_z_bottom,
    spar_radius,
    spar_radius,
)
```

The larger disk represents the complete footprint of the heave plate.

The smaller disk has exactly the same radius as the spar.

If we simply left these two surfaces overlapping, however, they would exist as separate geometric entities occupying the same region. Instead, we use a **fragment operation** to divide the large disk using the smaller disk.

```python
partitioned_entities, _ = gmsh.model.occ.fragment(
    [(2, outer_disk)],
    [(2, inner_disk)],
)
```

The result is a partitioned footprint containing:

1. a central disk with the spar radius; and
2. a surrounding annulus extending from the spar radius to the plate radius.

Conceptually, the original plate $0 \le r \le r_p$ has been divided into two conformal regions:
$0 \le r \le r_s$ and $r_s \le r \le r_p$.

!!! note "Why Partition the Plate?"
    The central disk provides a surface from which the spar can later be extruded. The surrounding annulus forms the remainder of the heave plate. Because the regions are created through a fragment operation, they share the same geometric interface rather than existing as overlapping independent surfaces.

!!! note "Cut vs. Fragment"
    In the heave-plate construction, both the central disk and annulus were retained because the central region was later extruded into the spar. For this annular body, the central region represents open water and should be removed entirely. A Boolean `cut()` is therefore the more appropriate operation.
    
After performing the fragment operation, we synchronize the OpenCASCADE geometry:

```python
gmsh.model.occ.synchronize()
```

We then collect the two resulting surfaces and verify that the expected partition was created:

```python
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
```

The `RuntimeError` acts as a useful safeguard. If the geometry construction does not produce exactly the expected two surfaces, the script stops rather than continuing with an invalid model.

### Set the Spar Circumferential Resolution

We next identify the inner and outer circular curves:

```python
inner_source_circle, outer_source_circle = (
    find_source_circles(
        source_surfaces=source_surfaces,
        spar_radius=spar_radius,
        plate_radius=plate_radius,
        source_z=plate_z_bottom,
    )
)
```

The inner circle corresponds to the spar radius and is given the same transfinite constraint used in the previous example:

```python
gmsh.model.mesh.setTransfiniteCurve(
    inner_source_circle,
    n_spar_circumference + 1,
)
```

This controls the number of panels around the spar circumference.

Importantly, the outer edge of the plate is **not** given a transfinite constraint. Its discretization will instead be governed by the unstructured plate mesh size introduced later.

### Extrude the Heave Plate

The two partitioned source surfaces are now extruded upward through the plate thickness:

```python
gmsh.model.occ.extrude(
    [(2, surface) for surface in source_surfaces],
    annulus_x0,
    annulus_y0,
    plate_thickness,
    numElements=[n_plate_thickness],
    recombine=True,
)
```

Both the central disk and surrounding annulus therefore move from $z=z_{\mathrm{bottom}}$ to $z=z_{\mathrm{top}}$.

The option

```python
numElements=[n_plate_thickness]
```

specifies the number of mesh layers through the thickness of the plate.

With

```python
n_plate_thickness = 2
```

the plate is divided into two layers through its thickness.

Finally,

```python
recombine=True
```

allows the vertical plate surfaces to form quadrilateral panels where possible.

We then synchronize again:

```python
gmsh.model.occ.synchronize()
```

At this point, the complete heave plate geometry exists, including the small central volume directly beneath the future spar.

---

## 4. Identify the Central Top Surface of the Plate

The next step is to locate the small circular surface at the center of the **top** of the heave plate.

```python
# =============================================================================
# 4. IDENTIFY THE CENTRAL TOP SURFACE OF THE PLATE
# =============================================================================
central_top_surface = find_central_horizontal_surface(
    target_z=plate_z_top,
    target_radius=spar_radius,
)
```

This surface is identified using the helper function discussed earlier. Rather than assuming a particular surface tag, the function searches for a surface that is:

* horizontal;
* located at $z=\texttt{plate_z_top}$; and
* approximately equal in area to a circle having the spar radius.

The expected area is $A_s=\pi r_s^2$.

Once the correct surface has been identified, it becomes the starting surface for the spar extrusion.

```python
gmsh.model.occ.extrude(
    [(2, central_top_surface)],
    0.0,
    0.0,
    spar_height,
    numElements=[n_spar_axial],
    recombine=True,
)
```

The extrusion vector is $(0,0,H_s)$, so the central surface is extended vertically upward to create the spar.

The axial resolution is again specified directly using

```python
numElements=[n_spar_axial]
```

and `recombine=True` creates quadrilateral panels along the cylindrical wall.

Because the central circle inherited its circumferential discretization from the original partitioned plate geometry, the structured mesh continues naturally upward into the spar.

!!! note "Staged Extrusion"
    The heave plate and spar are not constructed as independent overlapping cylinders. Instead, the geometry is built progressively from shared surfaces. This **staged extrusion** creates conformal interfaces between neighboring volumes and allows the mesh topology to remain consistent across the complete body.

After creating the spar, the geometry is synchronized once again:

```python
gmsh.model.occ.synchronize()
```

---

## 5. Extract the Exterior Boundary

The geometry now contains several three-dimensional construction volumes:

* the annular portion of the heave plate;
* the central portion of the heave plate beneath the spar; and
* the spar itself.

These volumes share internal interfaces. Those internal surfaces are useful during construction, but they should **not** be included in the final hydrodynamic mesh.

```python
# =============================================================================
# 5. EXTRACT THE EXTERIOR BOUNDARY
# =============================================================================

volumes, exterior_surfaces = get_exterior_surfaces()
```

The helper function retrieves the boundary of all volumes simultaneously:

```python
combined_boundary = gmsh.model.getBoundary(
    volumes,
    combined=True,
    oriented=False,
    recursive=False,
)
```

The important option here is:

```python
combined=True
```

When the boundaries are evaluated together, shared internal interfaces cancel, leaving only the surfaces that bound the complete assembly.

We then compare those exterior surfaces against all two-dimensional surfaces in the model:

```python
all_surfaces = {
    tag
    for dimension, tag in gmsh.model.getEntities(2)
}

internal_surfaces = sorted(
    all_surfaces - set(exterior_surfaces)
)
```

This gives us separate lists of:

* **exterior surfaces**, which belong in the final body mesh; and
* **internal construction surfaces**, which should be excluded.

### Create a Physical Group

The exterior surfaces are then collected into a Gmsh **physical group**:

```python
wetted_surface_group = gmsh.model.addPhysicalGroup(
    2,
    exterior_surfaces,
)

gmsh.model.setPhysicalName(
    2,
    wetted_surface_group,
    "Wetted surface",
)
```

A physical group provides a way to assign a meaningful name to a collection of geometric entities.

In this case, all exterior surfaces are grouped under the name:

```text
Wetted surface
```

This group will later be used to control which surfaces are written to the output mesh file.

!!! note "Construction Geometry vs. Computational Geometry"
    The surfaces required to *construct* a geometry are not always the same surfaces required by the numerical model. Internal interfaces help us build a conformal solid, but Capytaine ultimately needs only the exterior body boundary.

---

## 6. Set the Unstructured Plate-Face Resolution

The spar circumference, spar height, and plate thickness already have explicit mesh controls. We now specify the approximate resolution of the larger horizontal heave-plate surfaces.

```python
# =============================================================================
# 6. SET THE UNSTRUTURED PLATE-FACE RESOLUTION
# =============================================================================

gmsh.model.mesh.setSize(
    gmsh.model.getEntities(0),
    plate_mesh_size,
)

gmsh.option.setNumber(
    "Mesh.MeshSizeMax",
    plate_mesh_size,
)
```

The first command assigns the desired mesh size to the geometric points in the model:

```python
gmsh.model.mesh.setSize(
    gmsh.model.getEntities(0),
    plate_mesh_size,
)
```

For this example,

```python
plate_mesh_size = 0.05
```

so Gmsh is instructed to use an approximate characteristic length of $0.05~\mathrm{m}$ when generating the unstructured regions of the mesh.

The second command places an upper bound on element growth:

```python
gmsh.option.setNumber(
    "Mesh.MeshSizeMax",
    plate_mesh_size,
)
```

Together, these settings control the approximate resolution of the unstructured triangular mesh on the horizontal plate faces.

The transfinite constraint previously applied to the inner circle still governs the exact circumferential resolution of the spar.

This means the completed body contains two complementary meshing strategies:

* **structured extrusion controls** for the spar and plate thickness; and
* **unstructured size-based meshing** for the broad horizontal plate faces.

---

## 7. Generate and Write the Mesh

With the geometry and mesh controls complete, we can generate the two-dimensional surface mesh:

```python
gmsh.model.mesh.generate(2)
```

As before, we request a surface mesh because the eventual hydrodynamic analysis uses a Boundary Element Method.

### Remove Duplicate Nodes

The script then includes an additional cleanup step:

```python
gmsh.model.mesh.removeDuplicateNodes()
```

Because the model was constructed using conformal fragmented and extruded surfaces, we should not normally expect large numbers of duplicate nodes.

Nevertheless, this command provides an additional safeguard by removing coincident nodes if they occur.

### Report the Surface Elements

The helper function

```python
report_surface_elements(exterior_surfaces)
```

examines the exterior mesh and prints the number of each element type.

For example, the output may contain counts for:

* triangles;
* quadrilaterals; and
* the total number of surface elements.

This is useful because the mesh intentionally contains both triangular and quadrilateral panels.

It also gives us a convenient way to monitor mesh size as the resolution parameters are changed.

### Export Only the Exterior Boundary

Before writing the mesh, we specify:

```python
gmsh.option.setNumber(
    "Mesh.SaveAll",
    0,
)
```

Setting `Mesh.SaveAll` to zero tells Gmsh to save only entities belonging to physical groups.

Since the physical group created earlier contains only the exterior surfaces, the internal construction interfaces are omitted from the output file.

The mesh is then written using:

```python
fout = "../meshes/" + mesh_fname + ".msh"
gmsh.write(fout)
```

With the current filename,

```python
mesh_fname = 'spar_with_heave_plate'
```

the resulting file is

```text
../meshes/spar_with_heave_plate.msh
```

!!! warning "Why Exclude Internal Surfaces?"
    Internal construction surfaces do not represent boundaries between the body and the surrounding fluid. Including them in the exported hydrodynamic mesh would introduce surfaces that do not physically belong to the wetted exterior of the body.

---

## 8. Finalize

The final step is unchanged from the previous example:

```python
# =============================================================================
# 8. FINALIZE
# =============================================================================
# This closes the Gmsh API session.

gmsh.finalize()
```

This closes the Gmsh API session and releases its associated resources.

---

## Understanding the Construction Strategy

Although the completed geometry looks like a simple spar attached to a circular plate, the underlying construction has been designed specifically to provide control over the mesh.

The process can be summarized as $\text{Partition Plate}\rightarrow\text{Extrude Plate}\rightarrow\text{Identify Central Surface}\rightarrow\text{Extrude Spar}$.

The initial fragmentation step establishes a circular interface at the spar radius. Because that interface becomes part of the subsequent extrusions, the mesh can remain conformal as the geometry is extended from the plate into the spar.

The final surface mesh therefore combines several different resolution controls:

* `n_spar_circumference` controls the spar circumference;
* `n_spar_axial` controls the spar height;
* `n_plate_thickness` controls the plate thickness; and
* `plate_mesh_size` controls the approximate resolution of the horizontal plate surfaces.

This is more flexible than applying one global element size to the complete body.

It also illustrates an important principle in computational meshing: **the way a geometry is constructed can be just as important as the final shape itself**. By designing the underlying topology carefully, we gain much greater control over how that geometry is discretized.

!!! success "Spar with Heave Plate Complete"
    We have now extended the simple spar mesh into a compound geometry containing both structured and unstructured surface regions. In the next section, we will use similar ideas to prepare the complete floating body for hydrodynamic analysis.
