Capytaine is an open-source boundary element method (BEM) solver used to analyze the interaction between ocean waves and floating bodies. It computes key hydrodynamic coefficients such as added mass, radiation damping, wave excitation forces, and hydrostatic properties that form the foundation for modeling wave energy converters, offshore structures, and other marine systems.

Unlike computational fluid dynamics (CFD) software, Capytaine uses potential flow theory to efficiently predict wave-body interactions, making it well suited for early-stage design studies and hydrodynamic analysis.

## Capytaine Environment
In this course, we will use a dedicated Conda environment named ++"capytaine"++ to manage the Python packages required for Capytaine. Using an isolated environment helps avoid conflicts between package versions and keeps the numerical modeling workflow self-contained and reproducible.

!!! warning "Is Conda Installed?"
    If Conda has not yet been installed, refer to the [Miniconda setup](https://hmec-uh.github.io/work_environments/python/conda/) instructions before proceeding.

!!! warning "Is Spyder Installed?"
    If Spyder has not yet been installed, refer to the [Spyder IDE](https://hmec-uh.github.io/work_environments/python/spyder_ide/) instructions before proceeding.

!!! warning "Mesh Created?"
    It is assumed that you have generated a mesh (e.g., [Gmsh](../Gmsh/gmsh.md#gmsh)) and defined the ++"capytaine"++ environment. 

To start, open a terminal and activate your ++"capytaine"++ environment:

    conda activate capytaine

As a reminder, you should see the environment name to the left of your terminal command prompt:

![Active Env](assets/images/activate_env.png){#terminal-env}

*Figure 1: Active terminal environment.*

Using the [Conda package manager](https://capytaine.org/stable/user_manual/installation html#installing-with-conda-package-manager), install Capytaine with

    conda install --channel conda-forge capytaine 

!!! note "Optional Packages"
    The [Capytaine docs](https://capytaine.org/stable/user_manual/installation html#installing-with-conda-package-manager) also point out a few optional packages you can install:

        conda install --channel conda-forge jupyter matplotlib vtk

    The packages above are not required for Capytaine itself, but they are commonly used for notebook workflows, plotting, and visualization.

To later connect this environment to Spyder, install the Spyder kernel package:

    conda install spyder-kernels

This package allows Spyder to execute Python code using the interpreter and packages installed within the ++"capytaine"++ environment rather than the default Conda environment.

Your ++"capytaine"++ environment should now be ready for use. In the next section, we will configure Spyder to use this environment so that Capytaine and its dependencies are available directly within the development environment.

## Spyder Configuration

Next we need to launch the [Spyder IDE](https://hmec-uh.github.io/work_environments/python/spyder_ide/). In this course, Spyder is installed in a separate Conda environment named ++"spyder"++. Keeping the development environment separate from project-specific environments avoids duplicate installations and allows Spyder to be reused across multiple projects. Other approaches are possible, including installing Spyder directly into each project environment or using a system-wide installation.

Launch a new terminal, but keep the previous one active in case you need to later install additional programs in your ++"capytaine"++ environment. If you followed along with the [Spyder IDE](https://hmec-uh.github.io/work_environments/python/spyder_ide/) installation, you should also have a ++"spyder"++ virtual environment. Activate this environment **in your new terminal**:

    conda activate spyder

Launch Spyder by executing:

    spyder

Once Spyder is up and running, we can configure it to use the Python interpreter associated with the ++"capytaine"++ environment. This allows Spyder to execute code using the packages installed within that environment, including Capytaine and other scientific computing libraries.

To configure the interpreter:

1. Open `Tools > Preferences > Python Interpreter`
2. Select `Selected Interpreter`
3. Browse to the Python executable associated with the ++"capytaine"++ environment

![Select Interpreter](assets/images/spyder_set_env.png){#spyder-set-env}

*Figure 2: Point to Python interpreter in ++"capytaine"++ environment.*

During this course, we will create several three-dimensional plots that are easier to inspect interactively. In particular, interactive plotting allows us to rotate, pan, and zoom the view when inspecting our Capytaine meshes.

Often by default, Spyder displays Matplotlib figures within the Plots pane. To instead open figures in a separate interactive window, we need to change the Matplotlib graphics backend.

From the Spyder menu, 

1. Open `Tools > Preferences > IPython console`
2. Select `Selected Plotting`

Under ++"Graphics backend"++, select ++"Qt"++ from the drop-down menu. The ++"Tk"++ backend may also be used if Qt is unavailable.

![Select Interactive](assets/images/spyder_set_interactive.png){#spyder-set-inter}

*Figure 3: Configure Spyder to generate interactive plots.*

After applying the changes, close the current IPython console by clicking the ++"X"++ on the console tab. Spyder should automatically start a new console using the interpreter from the ++"capytaine"++ environment with interactive plotting enabled.

![Active Interpreter](assets/images/spyder_active_env.png){#spyder-active-env}

*Figure 4: Active newly defined interpreter.*

You can confirm the active interpreter by looking at the bottom of the window. It should say ++"capytaine"++ like in Figure 3 above. You can also verify the Capytaine installation directly from the IPython console:

    import capytaine as cpt
    cpt.__version__

If a version number is returned without errors, Spyder is successfully connected to the ++"capytaine"++ environment.


