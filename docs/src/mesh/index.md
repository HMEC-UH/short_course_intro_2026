# Overview
Many engineering problems are governed by equations that are defined over **continuous** domains. In fluid dynamics, for example, quantities such as pressure, velocity, and potential vary continuously throughout space. In theory, these governing equations apply at an infinite number of points on the surface of a body and throughout the surrounding fluid.

Computers, however, cannot solve problems over truly continuous domains. Instead, the physical system must first be converted into a **discrete** numerical representation. This process is called **discretization**.

A **mesh** is one of the primary ways this discretization is performed.

For marine hydrodynamics, the geometry of a floating body is divided into many smaller regions called **elements**, **faces**, or **panels**. Together, these panels approximate the original continuous surface of the body. Numerical methods then solve the governing equations over these smaller subdomains rather than over the exact continuous geometry.

Depending on the numerical method being used, the governing equations may be solved:

* at discrete node locations,
* over finite surface panels,
* over finite volumes,
* or through weighted approximations between neighboring elements.

In Capytaine, the hydrodynamic problem is formulated using a **Boundary Element Method (BEM)**. Rather than discretizing the entire fluid volume, only the wetted body surface is discretized into panels. The governing potential-flow equations are then solved over these surface elements to estimate quantities such as:

* added mass,
* radiation damping,
* excitation forces,
* hydrostatic properties,
* and wave-body interactions.

Because the mesh becomes the computational representation of the geometry, mesh quality directly affects the numerical solution. A mesh that is too coarse may poorly approximate the body shape and produce inaccurate hydrodynamic coefficients. On the other hand, a mesh that is excessively refined can dramatically increase computational cost without necessarily improving the solution in a meaningful way.

Good mesh generation therefore involves balancing:

* geometric fidelity,
* numerical stability,
* solution accuracy,
* and computational efficiency.

For this introductory course, the goal is not to produce an industrial-grade mesh, but rather to develop a clean, well-behaved mesh that appropriately represents the body geometry for hydrodynamic analysis.

## Mesh Generation Tools
There are many software packages capable of generating computational meshes. Different tools are often optimized for different numerical methods, geometries, and simulation workflows. Some focus on finite element analysis (FEA), others on computational fluid dynamics (CFD), and others on boundary element methods (BEM) such as those used in marine hydrodynamics.

Capytaine supports several common mesh formats, including meshes associated with Nemoh, WAMIT, Gmsh, STL, VTK/ParaView, Tecplot, and SALOME. Capytaine also includes simple built-in mesh generators for basic geometries such as spheres, cylinders, rectangles, disks, and parallelepipeds. See the [official documentation](https://capytaine.org/stable/user_manual/mesh.html#) for more information.

In this course, we will focus on **Gmsh** because it is:

* open source,
* widely used in scientific computing,
* relatively lightweight,
* capable of generating high-quality surface meshes for custom geometries,
* and supported through both a graphical interface and a Python API.

The Python interface is particularly useful because it allows mesh generation to become part of a larger computational workflow. Rather than manually creating geometries and exporting files through the graphical user interface alone, meshes can also be generated, modified, refined, and processed programmatically. This enables tighter integration with numerical modeling frameworks, parameter studies, optimization routines, and automated simulation pipelines.

Gmsh can export `.msh` files that are directly compatible with Capytaine, making it a practical workflow for preparing body geometries prior to hydrodynamic analysis.

Within the context of this course, Gmsh should be viewed as the tool used to convert a geometry into a discretized computational surface, while Capytaine uses that discretized mesh to solve the hydrodynamic problem numerically.

As students progress beyond introductory examples, programmatic mesh generation can become increasingly valuable for:

* generating families of related geometries,
* automating mesh refinement studies,
* modifying device parameters,
* and integrating geometry generation directly into Python-based simulation workflows.
