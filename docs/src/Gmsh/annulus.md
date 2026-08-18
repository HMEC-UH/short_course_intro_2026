In the previous section, we created a spar with an attached heave plate as a single continuous body. We will now create a second body: an **annulus** that surrounds the spar and is free to move independently.

Although the annulus is geometrically simple, it introduces an important distinction. The annulus is **not physically connected to the spar**, so the two bodies should not share mesh nodes or panels. Instead, a small water-filled clearance is maintained between the spar and the inner wall of the annulus.

The construction follows the same general extrusion-based approach used for the heave plate:

1. define the annulus geometry and mesh parameters;
2. initialize Gmsh;
3. create an annular source surface and extrude it;
4. identify the exterior surface of the resulting volume;
5. mark those surfaces for export;
6. control the resolution of the unstructured faces;
7. generate and write the mesh;
8. report the mesh composition; and
9. finalize the Gmsh session.

---

## 1. User-Defined Parameters

We begin by defining the spar radius, annulus dimensions, radial clearance, mesh resolution, and output names.

```python
# =============================================================================
# 1. USER-DEFINED PARAMETERS
# =============================================================================

# Spar geometry ---------------------------------------------------------------
spar_radius = 0.0301625  # Cylinder radius [m] (2.375" dia)


# Annulus geometry ------------------------------------------------------------
annulus_outer_radius = 0.483        # Cylinder height [m] (19 in)
annulus_height = 0.305              # Cylinder height [m] (12 in)


# Water-filled radial gap between the spar and annulus.
radial_clearance = 0.0254/2  # 0.5 in

# Annulus coordinates
annulus_x0 = 0.0
annulus_y0 = 0.0
annulus_z0 = 0.0

# Mesh Resolution -------------------------------------------------------------
# Number of panels through the vertical height of the annulus.
n_annulus_vertical = 6

# Approximate mesh size on the annulus top and bottom faces.
annulus_mesh_size = 0.05

# Names------------------------------------------------------------------------
model_name = 'annular_body'
mesh_fname = 'annular_body'
```

The spar radius, $r_s$, is retained because it determines the size of the opening through the annulus. The annulus itself is defined by an outer radius $r_o = 0.483~\mathrm{m}$ and a vertical height $H_a = 0.305~\mathrm{m}$. 

Unlike the heave plate, however, the inner radius is not equal to the spar radius. A small radial clearance is intentionally introduced so that $r_i = r_s + c$, where $r_s$ is the spar radius and $c$ is the water-filled radial clearance.

The clearance for the present geometry is $c = \frac{0.0254}{2} = 0.0127~\mathrm{m}$. Therefore, $r_i=0.0301625 + 0.0127 = 0.0428625~\mathrm{m}$.

!!! note "Separate Hydrodynamic Bodies"
    The annulus and spar are intentionally modeled as separate bodies. The finite clearance between them represents a region occupied by water and prevents the two meshes from sharing nodes or surfaces.

The mesh is controlled in two ways:

```python
n_annulus_vertical = 6
annulus_mesh_size = 0.05
```

The first parameter controls the number of mesh layers along the vertical cylindrical walls. The second specifies an approximate element size on the horizontal top and bottom faces.

---

## 2. Initialize Gmsh

The initialization process is unchanged from the previous examples.

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

The annulus begins as a two-dimensional ring-shaped source surface.

We first create a large circular disk:

```python
outer_disk = gmsh.model.occ.addDisk(
    annulus_x0,
    annulus_y0,
    annulus_z0,
    annulus_outer_radius,
    annulus_outer_radius,
)
```

This disk represents the complete footprint of the annular body.

We then calculate a second disk for the inner radius:

```python
annulus_inner_radius = spar_radius + radial_clearance

inner_disk = gmsh.model.occ.addDisk(
    annulus_x0,
    annulus_y0,
    annulus_z0,
    annulus_inner_radius,
    annulus_inner_radius,
)
```

The smaller disk represents the opening around the spar.

### Form the Annular Surface
To convert the two overlapping disks into a single annular surface, we use a ++"Boolean cut"++ operation. The smaller inner disk is subtracted from the larger outer disk, leaving only the ring-shaped region between the two radii. Since the central region represents the opening around the spar, it is removed entirely from the geometry:

```python
annular_entities, _ = gmsh.model.occ.cut(
    [(2, outer_disk)],
    [(2, inner_disk)],
    removeObject=True,
    removeTool=True,
)
```

This is a Boolean **cut** operation. Conceptually, the resulting surface occupies $r_i \le r \le r_o$.

!!! note "Boolean Operations"
    A Boolean cut() is useful when one geometric object should be subtracted from another. Gmsh provides several other Boolean operations for combining or partitioning geometry. We will introduce another of these operations in the next section, where we construct the spar and heave plate.

The geometry is then synchronized:

```python
gmsh.model.occ.synchronize()
```

We next extract the resulting two-dimensional surface:

```python
annular_source_surfaces = [
    tag
    for dimension, tag in annular_entities
    if dimension == 2
]
```

and verify that exactly one annular source surface exists:

```python
if len(annular_source_surfaces) != 1:
    raise RuntimeError(
        "Expected one annular source surface, "
        f"but found {annular_source_surfaces}."
    )
```

This check ensures that the Boolean operation produced the geometry we expected.

The resulting surface is stored as

```python
annular_source_surface = annular_source_surfaces[0]
```

### Extrude the Annulus

The annular source surface is then extruded vertically:

```python
extrusion_entities = gmsh.model.occ.extrude(
    [(2, annular_source_surface)],
    annulus_x0,
    annulus_y0,
    annulus_height,
    numElements=[n_annulus_vertical],
    recombine=True,
)
```

The extrusion creates four primary exterior surfaces:

* the bottom annular face;
* the top annular face;
* the outer cylindrical wall;
* the inner cylindrical wall.

The vertical resolution of both cylindrical walls is controlled by

```python
numElements=[n_annulus_vertical]
```

so with

```python
n_annulus_vertical = 6
```

the annulus is divided into six layers over its height.

The approximate vertical panel height is therefore $\Delta z = \frac{H_a}{N_z} = \frac{0.305}{6} \approx 0.0508~\mathrm{m}$.

Finally,

```python
recombine=True
```

allows the extruded cylindrical surfaces to use quadrilateral panels where possible.

After the extrusion, the OpenCASCADE geometry is synchronized again:

```python
gmsh.model.occ.synchronize()
```

---

## 4. Identify the Exterior Surface of the Annulus Volume

The annular extrusion should create one three-dimensional volume.

We first retrieve all volume entities:

```python
volume_entities = gmsh.model.getEntities(3)
```

and verify that exactly one exists:

```python
if len(volume_entities) != 1:
    raise RuntimeError(
        "Expected one annulus volume, "
        f"but found {volume_entities}."
    )
```

This is another useful geometry check. If the model contains more or fewer than one volume, something unexpected occurred during construction.

We then retrieve the boundary of the volume:

```python
boundary_entities = gmsh.model.getBoundary(
    volume_entities,
    combined=True,
    oriented=False,
    recursive=False,
)
```

Since the boundary of a three-dimensional volume consists of two-dimensional surfaces, we retain only entities with dimension `2`:

```python
exterior_surfaces = sorted(
    tag
    for dimension, tag in boundary_entities
    if dimension == 2
)
```

For a simple annulus, we expect four surfaces:

1. top;
2. bottom;
3. outer cylindrical wall;
4. inner cylindrical wall.

The script therefore includes a check:

```python
if len(exterior_surfaces) != 4:
    print(
        "Warning: Expected four exterior surfaces "
        "for a simple annulus."
    )
```

Unlike the previous `RuntimeError` checks, this condition only produces a warning. The script can therefore continue while still alerting us that the geometry may not match the expected topology.

---

## 5. Mark the Annulus Surface for Export

Once the exterior surfaces have been identified, they are collected into a physical group:

```python
annulus_group = gmsh.model.addPhysicalGroup(
    2,
    exterior_surfaces,
)
```

We then assign the group a meaningful name:

```python
gmsh.model.setPhysicalName(
    2,
    annulus_group,
    "Annulus wetted surface",
)
```

The physical group serves two purposes.

First, it provides a meaningful identifier for the group of surfaces.

Second, it allows us to control which entities are written to the output mesh file.

!!! note "Wetted Surface"
    For hydrodynamic calculations, the important geometry is the surface in contact with the surrounding fluid. The physical group identifies the annulus surfaces that will form its hydrodynamic boundary.

---

## 6. Set the Unstructured Face Resolution

The vertical resolution of the cylindrical walls was already defined during extrusion. We now specify an approximate mesh size for the top and bottom annular faces.

```python
gmsh.model.mesh.setSize(
    gmsh.model.getEntities(0),
    annulus_mesh_size,
)
```

For this example,

```python
annulus_mesh_size = 0.05
```

so the target element size is approximately $0.05~\mathrm{m}$.

The top and bottom annular surfaces are meshed automatically using an unstructured triangular mesh.

We also define a maximum allowable mesh size:

```python
gmsh.option.setNumber(
    "Mesh.MeshSizeMax",
    annulus_mesh_size,
)
```

This prevents the generated elements from becoming substantially larger than the specified target size.

The completed mesh therefore uses two complementary controls:

* `n_annulus_vertical` for the structured vertical extrusion;
* `annulus_mesh_size` for the unstructured horizontal faces.

---

## 7. Generate the Mesh

Once the geometry and mesh controls are complete, we generate the two-dimensional surface mesh:

```python
gmsh.model.mesh.generate(2)
```

As with the previous examples, we generate a surface mesh because the body will ultimately be used in a Boundary Element Method calculation.

The script then removes any coincident duplicate nodes:

```python
gmsh.model.mesh.removeDuplicateNodes()
```

The geometry should already be conformal, so few or no duplicate nodes are expected. This step simply provides an additional cleanup safeguard.

Before exporting, we specify:

```python
gmsh.option.setNumber("Mesh.SaveAll",0)
```

With `Mesh.SaveAll` set to zero, Gmsh writes only entities belonging to a physical group.

Because the physical group contains only the annulus exterior surfaces, the exported file contains only the surface mesh required for the hydrodynamic model.

The output path is then constructed:

```python
fout = "../meshes/" + mesh_fname + ".msh"
```

and the mesh is written using:

```python
gmsh.write(fout)
```

With

```python
mesh_fname = 'annular_body'
```

the resulting file is

```text
../meshes/annular_body.msh
```

---

## 8. Mesh Summary Report

Before closing Gmsh, the script reports the types and numbers of surface elements in the completed mesh.

```python
element_types, element_tags, _ = (
    gmsh.model.mesh.getElements(dim=2)
)
```

This retrieves all two-dimensional mesh elements.

The script then loops through the returned element types:

```python
for element_type, tags in zip(
    element_types,
    element_tags,
):
```

and obtains the descriptive name associated with each type:

```python
element_name = (
    gmsh.model.mesh.getElementProperties(
        element_type
    )[0]
)
```

Finally, the number of elements is printed:

```python
print(
    f"  {element_name}: {len(tags)}"
)
```

Because the annulus uses both structured extrusion and unstructured face meshing, we should expect a combination of element types, primarily:

* quadrilaterals on the inner and outer cylindrical walls; and
* triangles on the top and bottom annular faces.

This report provides a quick way to verify the mesh composition and compare different mesh resolutions.

---

## 9. Finalize

The final step is to close the Gmsh API session:

```python
# =============================================================================
# 9. FINALIZE
# =============================================================================
# This closes the Gmsh API session.

gmsh.finalize()
```

As before, `gmsh.finalize()` releases the resources associated with the current Gmsh session and completes the script.

---

## Understanding the Annular Body

The basic construction can be summarized as: $\text{Outer Disk} - \text{Inner Disk} \rightarrow
\text{Annular Surface} \rightarrow \text{Extruded Annular Volume}$.

This is geometrically simpler than the spar-with-heave-plate model because the body consists of only one construction volume.

The important modeling distinction is that the inner radius is deliberately larger than the spar radius: $ r_i > r_s$. The difference, $c=r_i-r_s$, represents the water-filled gap between the two hydrodynamic bodies.

This gap ensures that the annulus and spar remain separate meshes with independent surfaces and nodes.

!!! warning "Do Not Merge the Bodies"
    The spar and annulus represent separate moving bodies. They should therefore not be fused into a single geometric volume or forced to share a common mesh interface. The fluid-filled gap between them must remain part of the hydrodynamic domain.

The meshing strategy follows the same philosophy introduced in the previous examples:

* use extrusion to control resolution in the direction where structured layers are useful;
* use an approximate element size for broad horizontal faces;
* identify the exterior boundary explicitly; and
* export only the surfaces required by the hydrodynamic model.

!!! success "Floating Body Mesh Complete"
    We have now created the second hydrodynamic body as an independent annular mesh surrounding the spar. With both meshes available, the next step is to place the bodies in their appropriate floating positions and assemble them into a multibody hydrodynamic model.
