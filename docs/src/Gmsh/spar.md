We will begin by creating the simplest component of our floating body: the **spar**. The spar is represented as a long vertical cylinder, making it a useful geometry for introducing the basic Gmsh workflow before moving on to the heave plate and the complete floating body.

In this example, we will also introduce an important meshing strategy. Rather than prescribing a single mesh size everywhere, we will control the mesh resolution independently in two directions:

* the number of elements along the **length of the spar** (axial resolution)
* the number of elements around its **circumference** (radial resolution)

This is particularly useful for long, slender geometries because the characteristic dimensions in these two directions are very different.

The complete script is organized into eight sections:

1. User-Defined Parameters
2. Initialize Gmsh
3. Create Geometry
4. Synchronize the Geometry
5. Set the Circumferential Resolution
6. Generate the Mesh
7. Write the Mesh to a File
8. Finalize

Each section is discussed below.

## 1. User-Defined Parameters

We begin by defining the geometric dimensions, coordinates, mesh resolution, and file names used throughout the script.

```python
# =============================================================================
# 1. USER-DEFINED PARAMETERS
# =============================================================================
# The cylinder is defined by:
#   - the center of the first circular face: (x, y, z)
#   - an axis vector: (dx, dy, dz)
#   - a radius
#
# All dimensions are specified in meters.

# Spar geometry ---------------------------------------------------------------
spar_radius = 0.0301625  # Cylinder radius [m] (2.375" dia)
spar_height = 6.096      # Cylinder height [m] (6.096 m ~ 20 ft)
 
# Spar coordinates
spar_x0 = 0.0
spar_y0 = 0.0
spar_z0 = 0.0

spar_dx = 0.0
spar_dy = 0.0
spar_dz = spar_height

# Mesh Resolution--------------------------------------------------------------

# Specify the number of mesh layers along the spar axis. This
# controls the axial resolution independently of the resolution
# around the circumference.
n_axial = 80

# Specify the number of mesh elements around the circular edge.
# This controls how accurately the mesh represents the cylinder's
# circular cross-section.
n_circumference = 24

# Names------------------------------------------------------------------------
model_name = 'spar_buoy_refined'
mesh_fname = 'spar_buoy_refined'
```

The first variables define the physical dimensions of the spar. In this case, the radius is
$r = 0.0301625 ~\mathrm{m}$ and the height is $H = 6.096~\mathrm{m}$. 

The next group of variables defines the location and direction of the spar. The bottom face is centered at $(x_0,y_0,z_0)=(0,0,0)$ and the cylinder axis is described using the vector $(dx,dy,dz)=(0,0,H)$.

Since only the z-component is nonzero, the spar extends vertically upward from $z=0$ to $z=H$.

!!! warning "Units"
    Gmsh itself is unitless. Throughout this course, however, all geometric dimensions will be specified in **SI units**, with lengths expressed in meters. This is important because the resulting meshes will later be used in hydrodynamic calculations with Capytaine.

!!! note "Local Coordinate System"
    At this stage, the geometry is being created in a convenient **local coordinate system**. Its final position relative to the free surface, center of gravity, or other bodies can be adjusted later when the mesh is used in a hydrodynamic model.

The next two parameters control the mesh resolution:

```python
n_axial = 80
n_circumference = 24
```

These values are defined separately because the spar has very different characteristic dimensions in the axial and circumferential directions. This allows us to refine the mesh in one direction without unnecessarily refining the other.

Finally, the model and output file names are stored as variables:

```python
model_name = 'spar_buoy_refined'
mesh_fname = 'spar_buoy_refined'
```

Defining these values near the top of the script makes it easier to create and compare multiple versions of a mesh.

---

## 2. Initialize Gmsh

Before any geometry can be created, we must initialize the Gmsh Python API and create a model.

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

The command

```python
gmsh.initialize()
```

starts the Gmsh API and prepares it to receive geometry, meshing, and file-writing commands.

!!! note "Check"
    Before initializing, the script checks whether Gmsh is already running:

    ```python
    if gmsh.isInitialized():
        gmsh.finalize()
    ```

    This can be useful when developing scripts interactively in an environment such as Spyder. If a previous run stopped before reaching `gmsh.finalize()`, the Gmsh API may still be initialized. This check ensures that the script begins with a clean session.

Once Gmsh has been initialized, we create a new model:

```python
gmsh.model.add(model_name)
```

The model name does not affect the geometry, but it provides a useful identifier when inspecting the model or working with multiple geometries.

!!! note "Start and Stop Gmsh"
    Most Gmsh scripts begin with `gmsh.initialize()` and end with `gmsh.finalize()`. These commands start and properly close the Gmsh API session.

---

## 3. Create Geometry

We will create the spar using the OpenCASCADE geometry kernel. Rather than creating the complete cylinder directly, we first create a circular surface and then **extrude** that surface along the spar axis.

```python
# =============================================================================
# 3. CREATE GEOMETRY
# =============================================================================
# Create the circular bottom surface of the spar. Since the two
# radii are equal, addDisk creates a circle rather than an ellipse.
bottom_disk = gmsh.model.occ.addDisk(
    spar_x0,
    spar_y0,
    spar_z0,
    spar_radius,
    spar_radius
)

# Extrusion--------------------------------------------------------------------
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
```

The first step is to create the circular bottom face:

```python
bottom_disk = gmsh.model.occ.addDisk(
    spar_x0,
    spar_y0,
    spar_z0,
    spar_radius,
    spar_radius
)
```

The `addDisk()` function creates a two-dimensional surface. It accepts two radii because the same function can also be used to create an ellipse. Since both radii are equal here, the resulting surface is circular.

We then extrude this disk along the spar axis:

```python
extruded_entities = gmsh.model.occ.extrude(
    [(2, bottom_disk)],
    spar_dx,
    spar_dy,
    spar_dz,
    numElements=[n_axial],
    recombine=True
)
```

The expression

```python
[(2, bottom_disk)]
```

identifies the entity to be extruded. Gmsh commonly refers to geometric entities using a **dimension-tag pair**. The first value specifies the entity dimension:

* `0` — point
* `1` — curve
* `2` — surface
* `3` — volume

Since `bottom_disk` is a surface, its dimension is `2`.

The next three arguments define the extrusion vector:

```python
spar_dx,
spar_dy,
spar_dz
```

Because only `spar_dz` is nonzero, the disk is extruded vertically to form the cylindrical spar.

### Axial Mesh Resolution

One advantage of using an extrusion is that we can prescribe the number of mesh layers created along the extrusion direction:

```python
numElements=[n_axial]
```

For this example,

```python
n_axial = 80
```

so the spar is divided into 80 axial layers.

The approximate spacing between layers is therefore $\Delta z = \frac{H}{N_z}$ or, for this geometry, $\Delta z = \frac{6.096}{80} = 0.0762~\mathrm{m}$.

The final option,

```python
recombine=True
```

instructs Gmsh to recombine triangular elements into quadrilateral elements where possible. Along the cylindrical wall, this produces a regular series of four-sided panels rather than splitting every panel into two triangles.

!!! note "Why Extrude a Disk?"
    Gmsh also provides an `addCylinder()` function that can create a cylinder directly. We use an extrusion here because it gives us direct control over the number of mesh layers along the cylinder axis. This will make it easier to independently control the axial and circumferential mesh resolution.

---

## 4. Synchronize the Geometry

The geometry created above exists within the OpenCASCADE geometry kernel. Before the rest of the Gmsh model can access those entities, we must synchronize the geometry.

```python
# =============================================================================
# 4. SYNCHRONIZE THE GEOMETRY
# =============================================================================
# After creating geometry with the OpenCASCADE kernel, we must
# synchronize it with the main Gmsh model before meshing.

gmsh.model.occ.synchronize()
```

The synchronization step can be thought of as updating the main Gmsh model with the geometry that has just been created.

A useful way to think about the workflow is: $\text{Create Geometry}\rightarrow\text{Synchronize}\rightarrow \text{Mesh}$.

Multiple OpenCASCADE geometry operations can be performed before synchronization. Once the geometry is complete, `synchronize()` makes the resulting points, curves, surfaces, and volumes available to the rest of the Gmsh API.

---

## 5. Set the Circumferential Resolution

The axial resolution was prescribed during the extrusion. We now need to control the number of mesh elements around the circular cross-section of the spar.

```python
# ------------------------------------------------------------
# 5. Set the circumferential resolution
# ------------------------------------------------------------
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
```

We first ask Gmsh for the geometric boundary of the bottom disk:

```python
bottom_boundary = gmsh.model.getBoundary(
    [(2, bottom_disk)],
    oriented=False,
    recursive=False
)
```

Since the disk is a two-dimensional surface, its boundary consists of one-dimensional curves. For this simple geometry, the boundary is the circular curve around the outside of the disk.

Gmsh returns these entities as dimension-tag pairs, so we extract the tags belonging to one-dimensional entities:

```python
bottom_curves = []

for dimension, tag in bottom_boundary:
    if dimension == 1:
        bottom_curves.append(tag)
```

For this simple disk, there is only one boundary curve, but storing the result in a list makes the code more general and prepares us for more complicated geometries later.

We then apply a **transfinite curve constraint**:

```python
gmsh.model.mesh.setTransfiniteCurve(
    curve,
    n_circumference + 1
)
```

A transfinite constraint gives Gmsh direct control over how many nodes are distributed along the curve. Because the number of nodes is one greater than the number of elements specified in this script, we use

```python
n_circumference + 1
```

to obtain the desired circumferential discretization.

With

```python
n_circumference = 24
```

the circular cross-section is divided into 24 circumferential segments.

At this point, the two primary mesh directions are controlled independently: $N_z = n_{\text{axial}}$ along the length of the spar, and $N_\theta = n_{\text{circumference}}$ around its circumference.

This is one of the main advantages of the present meshing strategy. For example, we could increase `n_axial` without changing the representation of the circular cross-section, or increase `n_circumference` without adding additional layers along the spar.

---

## 6. Generate the Mesh

With the geometry complete and the mesh constraints defined, we can generate the surface mesh.

```python
# =============================================================================
# 6. GENERATE THE MESH
# =============================================================================
# We will be most interested in the surface (2) mesh of the body rather than
# the full volume (3) mesh.

gmsh.model.mesh.generate(2)
```

The argument passed to `generate()` specifies the dimension of the mesh:

* `generate(1)` meshes curves,
* `generate(2)` meshes surfaces,
* `generate(3)` meshes volumes.

In this case, we use

```python
gmsh.model.mesh.generate(2)
```

because we are interested in the **surface mesh** of the spar.

This distinction is important for our later use of the mesh in Capytaine. Capytaine uses a **Boundary Element Method (BEM)**, so only the wetted surface of the body needs to be discretized. There is no need to fill the interior of the spar with three-dimensional elements.

!!! note "Volume Mesh"
    A volume mesh generated using `generate(3)` would be useful for other numerical methods, such as finite element analysis or some computational fluid dynamics methods, but it would add unnecessary elements for the present application.

---

## 7. Write the Mesh to a File

The mesh now exists in memory within the Gmsh model. To use it in other programs, we need to save it to a file.

```python
# =============================================================================
# 7. WRITE THE MESH TO A FILE
# =============================================================================
# The .msh format is Gmsh's native mesh format.

fout = "../meshes/" + mesh_fname + ".msh"
gmsh.write(fout)
```

The output path is assembled from the previously defined mesh name:

```python
fout = "../meshes/" + mesh_fname + ".msh"
```

With

```python
mesh_fname = 'spar_buoy_refined'
```

the resulting path becomes

```text
../meshes/spar_buoy_refined.msh
```

The `.msh` format is Gmsh's native mesh format and preserves the mesh geometry and element information needed for later processing.

The `..` in the file path refers to the **parent directory** of the current working directory. The script therefore assumes that a folder named `meshes` exists one level above the directory from which the script is being run.

!!! warning "Relative File Paths"
    Relative paths are interpreted from Python's current **working directory**, which is not necessarily the same as the folder containing the Python script. If Gmsh reports that it cannot write the output file, check the current working directory in Spyder and verify that the `../meshes/` folder exists.

Finally, the mesh is written using:

```python
gmsh.write(fout)
```

---

## 8. Finalize

Once the geometry has been created, meshed, and written to disk, we properly close the Gmsh API session.

```python
# =============================================================================
# 8. FINALIZE
# =============================================================================
# This closes the Gmsh API session.

gmsh.finalize()
```

The `gmsh.finalize()` command releases the resources associated with the current Gmsh session.

Although a short script may sometimes terminate without explicitly calling `finalize()`, including it is good practice and ensures that the API session is closed cleanly.

---

## Resulting Mesh

The resulting spar mesh is structured primarily in two directions: axially along the length of the spar and circumferentially around its circular cross-section.

For the present example,

```python
n_axial = 80
n_circumference = 24
```

the cylindrical wall is divided into approximately $80 \times 24 = 1920$ quadrilateral panels.

Additional elements are required to mesh the circular top and bottom faces, so the complete surface mesh contains somewhat more than 1920 elements.

The more important point is that the two directions can be refined independently. For example,

```python
n_axial = 120
n_circumference = 24
```

would increase the resolution along the spar without changing the number of elements around its circumference.

Alternatively,

```python
n_axial = 80
n_circumference = 48
```

would provide a finer approximation of the circular cross-section without changing the axial spacing.

!!! note "Mesh Resolution"
    A finer mesh is not automatically a better mesh. Increasing the number of panels increases computational cost, and additional refinement may eventually have little effect on the calculated hydrodynamic coefficients. Later, we will evaluate mesh resolution through a **mesh convergence study** in Capytaine.

!!! success "Spar Mesh Complete"
    We have now created the first component of the floating-body mesh. More importantly, we have introduced a meshing strategy that allows the axial and circumferential resolution to be controlled independently. In the next section, we will build on this approach to create the heave plate.
