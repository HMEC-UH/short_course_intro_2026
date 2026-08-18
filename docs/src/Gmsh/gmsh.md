The goal of the instructions below is to introduce practical mesh generation workflows in Gmsh for hydrodynamic analysis with Capytaine using the Gmsh Python API. Rather than reproducing the full Gmsh user manual, this section focuses on the concepts and workflows most relevant to marine energy applications, including creation of simple parametric meshes that can be integrated directly into Python-based simulation workflows, as well as construction of basic non-parametric geometries entirely from code. The objective is to develop a practical foundation for building and modifying computational meshes while developing intuition for how geometry discretization influences numerical hydrodynamic models.

# Gmsh
In this course, we will use a dedicated Conda environment named ++"capytaine"++ to manage the Python packages required for Capytaine and Gmsh. Using an isolated environment helps avoid conflicts between package versions and keeps the numerical modeling workflow self-contained and reproducible.

!!! warning "Is Conda Installed?"
    If Conda has not yet been installed, refer to the earlier [Miniconda setup](https://hmec-uh.github.io/work_environments/python/conda/) instructions before proceeding.

!!! note "Conda ++"channel"++"
    After entering Conda commands, you will be prompted with a yes/no to proceed. Herein, I'm going to assume you say "yes" and everything goes smoothly — fingers crossed!

We will start by creating a new Conda environment:

    conda create -n capytaine python=3.11

This command creates a new environment named ++"capytaine"++ with Python 3.11 installed.

It is worth pausing for a moment to appreciate what just happened. Rather than manually downloading libraries, configuring paths, or resolving conflicting package versions, Conda manages the required software stack for you. Installing Python packages through Conda not only installs the requested package itself, but also the supporting libraries required for the associated numerical workflow. We will continue to see this pattern throughout the course — dependencies are automatically handled by Conda, the package manager.

With the new environment created, we need to **activate** it:

    conda activate capytaine

You should now see ++"capytaine"++ in parenthesis leading your command prompt.

Once activated, install Gmsh from the ++conda-forge++ channel:

    conda install -c conda-forge gmsh

Gmsh should now be installed!

!!! note "Conda ++"channel"++"
    A Conda **channel** is similar to an app store that hosts software packages. Different channels serve different purposes, and ++conda-forge++ is a large community-maintained channel widely used in scientific computing and engineering workflows. Many open-source numerical modeling tools are distributed and updated through ++conda-forge++, making it the preferred source for packages such as Gmsh and Capytaine.

Gmsh includes a Python [Application Programming Interface (API)](https://gmsh.info/doc/texinfo/gmsh.html#Gmsh-application-programming-interface), which allows geometry creation, mesh generation, refinement, and export operations to be performed directly from Python code. In this course, we will primarily interact with Gmsh through this API rather than through the graphical user interface. This approach allows mesh generation to become part of larger computational workflows that can be automated, parameterized, and integrated directly with Capytaine simulations.

The [Spyder IDE](https://hmec-uh.github.io/work_environments/python/spyder_ide/) was introduced previously in the Python setup instructions. To allow Spyder to interface with our ++"capytaine"++ environment, we first need to install the appropriate communication kernels inside the ++"capytaine"++ environment:

    conda install spyder-kernels

Once installed, open a **new command prompt** window and activate the separate ++"spyder"++ environment created earlier:

    conda activate spyder

Launch the Spyder IDE by typing:

    spyder

Once Spyder is running, we can configure it to use the Python interpreter associated with the ++"capytaine"++ environment. This allows Spyder to execute code using the packages installed within that environment, including Gmsh and other scientific computing libraries.

To configure the interpreter:

1. Open ++"Tools → Preferences → Python Interpreter"++
1. Select ++"Selected interpreter"++
1. Browse to the Python executable associated with the ++"capytaine"++ environment

![Python interpreter](assets/images/python_interpreter.png){#python-interp}
*Figure 1: Select python interpreter from environment.*

The interpreter path will depend on the operating system and Conda installation location. For example:

<details markdown="1">
  <summary>Windows</summary>
    C:\Users\troy\miniconda3\envs\capytaine\python.exe
</details>

<details markdown="1">
  <summary>Linux</summary>
    /home/troy/miniconda3/envs/capytaine/bin/python
</details>

After applying the changes, restart the Spyder console if prompted. Spyder should now be running directly from the ++"capytaine"++ environment.

We are now ready to begin creating computational mesh models in Gmsh using the Python API. Throughout the remainder of this chapter, geometry creation, mesh generation, refinement, and export operations will all be performed directly from Python code.
