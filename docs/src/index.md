There are three primary tools used to numerically evaluate a wave energy converter (WEC):

* Mesh generator (e.g., [Gmsh](https://gmsh.info/))
* Solver for hydrodynamic coefficients (e.g., [Capytaine](https://capytaine.org/stable/))
* Multibody simulation environment for 3D mechanical systems (e.g., [WEC-Sim](https://wec-sim.github.io/WEC-Sim/main/index.html))

The links in parentheses correspond to the tools primarily used at HMEC. While other tools are available, the framework above is widely used in the university-level wave energy community due to the open-source availability of these packages and the broad accessibility of MATLAB for researchers.

The first two software packages are fully open source and can be used entirely within a Python-based workflow. The third, however, is better described as an open-source toolbox built around MATLAB. While the toolbox itself is openly available, running simulations still requires a licensed MATLAB installation.
