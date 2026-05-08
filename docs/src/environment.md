# Setup Your Environment

There are three primary tools used to numerically evaluate a wave energy converter:

* Mesh generator (e.g., [Gmsh](https://gmsh.info/))
* Solver for hydrodynamic coefficients (e.g., [Capytaine](https://capytaine.org/stable/))
* Multibody simulation environment for 3D mechanical systems (e.g., [WEC-Sim](https://wec-sim.github.io/WEC-Sim/main/index.html))

The links in parentheses correspond to the tools primarily used at HMEC. While other tools are available, the framework above is widely used in the university-level wave energy community due to the open-source availability of these packages and the broad accessibility of MATLAB for researchers.

The first two software packages are fully open source and can be used entirely within a Python-based workflow. The third, however, is better described as an open-source toolbox built around MATLAB. While the toolbox itself is openly available, running simulations still requires a licensed MATLAB installation.

## Python
Python is often included as part of the operating system environment, particularly on Linux systems. Regardless of the platform, it is good practice to create isolated Python **virtual environments** for project work rather than using the system-wide installation directly. This helps avoid dependency conflicts and prevents accidental changes to OS-level utilities or packages that may rely on the system Python installation.

!!! warning "Virtual Environments"
    Working in a virtual environment avoids dependency conflicts and prevents accidental changes to OS-level utilities
    
### Conda
Managing Python dependencies manually is generally impractical for computing workflows. Fortunately, several package managers are available to simplify environment and dependency management. At HMEC, the primary package manager used is "Conda", which is distributed through several interfaces and installations, including:

* Anaconda — a full scientific Python distribution that includes Conda along with many pre-installed packages and graphical tools (large installation)
* Miniconda — a lightweight Conda installer that provides only the core package and environment manager
* Miniforge — a community-maintained Conda distribution that emphasizes open-source packages and the conda-forge ecosystem

For most users in this course, Miniconda or Miniforge will be sufficient and are generally preferred due to their smaller installation size and greater flexibility.




