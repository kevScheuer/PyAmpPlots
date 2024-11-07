# Introduction
This repository serves as a beginner's guide for using python to plot partial wave analysis fits from AmpTools. To get started, follow the quick **Setup** instructions below, and see the [jupyter notebook tutorial](./analysis/tutorial.ipynb). It is assumed you are a beginner to extracting and plotting fit results, but have a basic understanding of how AmpTools partial wave analyses work. If not, make sure to check the tutorials and guides at it's [github](https://github.com/mashephe/AmpTools).

# :hammer_and_wrench: Setup
:warning: This repo must be cloned to an ifarm node :warning:

To run the scripts within this repository we will need 2 things:
1. A working ROOT build that can load AmpTools libraries
2. A python environment based off the ifarm's current default python version (3.9.18)

Luckily all these things are provided to you here for immediate and easy setup! First you'll want to `git clone` this repository into a directory on the ifarm, preferably within your own `/w/halld-scshelf2101/home/$USER/` directory.

## $\color{Turquoise}\sqrt{~}$ ROOT  
To load ROOT and AmpTools we will use the standard GlueX builds for each. These will add all the necessary libraries and binaries to our path. All you need to do is run:
```
source setup_gluex.csh # if using a tcsh/csh shell (the ifarm default) or
source setup_gluex.sh # if using bash 
```
Next we want to have the AmpTools classes available for ROOT to load. Copy the `.rootrc` file to your home directory  by running: 
```
cp .rootrc ~/
``` 
This file simply adds a path that will allow us to utilize the AmpTools `FitResults` class. Execute `root` in a terminal window, then run `.x loadAmpTools.C` in the ROOT session. If this is successful, you should see the following output:
```
--------------------------------------------------
------      Loading AmpTools Modules        ------
--------------------------------------------------
Loading IUAmpTools/report.cc..
Loading IUAmpTools/Kinematics.cc..
Loading IUAmpTools/ConfigurationInfo.cc..
Loading IUAmpTools/ConfigFileParser.cc..
Loading IUAmpTools/NormIntInterface.cc..
Loading IUAmpTools/FitResults.cc..
--------------------------------------------------
------  Finished Loading AmpTools Modules   ------
--------------------------------------------------
```

## :snake: Python
We will be using very basic python virtual environments (venv) to keep our python versions and packages consistent. Starting in the parent `PyAmpPlots` folder, execute
```
python -m venv .venv
``` 
to create a virtual environment with the same python version as the ifarm default. Activate the environment by running 
```
source .venv/bin/activate
``` 
(use `activate.csh` for csh/tcsh shells). With our new virtual environment, we can now download the required python packages to perform our analysis. Run
```
python -m pip install -r requirements.txt
```
to download these packages to the virtual environment.

NOTE: If you would like to contribute to this repository, please use the python Black formatter (included in the virtual environment and recommended vs code extensions) to keep the code formatting consistent

## :computer: VS Code
If you are using VS Code, you may have noticed a pop-up asking if you want to install the recommended extensions. These are of course just recommendations and not strictly needed, but I've found them to be greatly beneficial to my workflow.

# :question: FAQ
As stated in the intro, the best place to get started is the [jupyter notebook tutorial](./analysis/tutorial.ipynb), which will take you step-by-step through aggregating fit results and plotting them.

## How can I adopt this for my own analysis?
This tutorial uses a vector-pseudoscalar process $\gamma p \rightarrow \omega\pi^0$ for its amplitude analysis example. As such, the scripts will require some modification to be adapted for other channels / processes. Below discusses what needs to be modified.

### Amplitude Naming
When naming amplitudes like `reaction::sum_type::amp_name` there is unfortunately no single standard that enforces what `amp_name` looks like. This repo follows the vector-pseudoscalar inspired format, where `amp_name = eJPmL`, explained in the table below.

| Quantum Number | Description | Allowed Characters |
| :------------: | :---------- | :----------------: | 
| e              | reflectivity | p (+), m (-) |
| J              | total spin   | positive integers including 0 |
| P              | parity       | p (+), m (-) |
| m              | spin-projection | p (+1), 0, m (-1) |
| L              | orbital angular momentum | standard letter convention: S, P, D, F, ... |

Note that this forces the m-projection to be a single character. If your config files, and therefore `.fit` result files, don't follow this format then you must edit the `parse_amplitude` function within [extract_fit_results.cc](./scripts/extract_fit_results.cc) to properly convert your amplitude naming scheme into `eJPmL` format. This is because the csv headers use this format, and so all the analysis scripts *heavily* depend on this for interpreting the results. You can, of course, choose to keep your `amp_name` scheme and instead rewrite all the analysis scripts to interpret your format instead.

### Data File Format
The [extract_bin_info.cc](./scripts/extract_bin_info.cc) script also makes 2 basic assumptions:
1. The flat ROOT trees (typically output by a DSelector) that serve as the input to AmpTools have cuts already applied to them in a mass bin. For example, the `M4Pi` branch in any of the mass bins in [data](./data/) is already cut to its alloted range. 
2. The following branches exist in each file:
    * `t`: the squared four momentum transfer
    * `E_Beam`: beam photon energy
    * `M4Pi`: the invariant mass spectrum of interest. There is an optional argument in the scripts to specify the name of this branch, but it still assumes that *a* mass branch exists.
    * `Weight`: tracks a weight value for each event so that sideband subtraction is properly implemented. This may fail when using a separate `background` file in the AmpTools config files.