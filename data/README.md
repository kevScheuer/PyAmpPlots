Contained here is pseudo-data for us to test out our amplitude analysis plotter on. The data is organized into bins of $\omega\pi^0$ invariant mass (GeV), which all contain a cut on the squared four-momentum transfer $-t$ from $0.3 < -t < 0.5$. The data was generated with $b_1(1235)$ and $\rho(1450)$ Breit-Wigner lineshapes, with their masses and widths fixed to [PDG values](https://pdglive.lbl.gov/ParticleGroup.action?init=0&node=MXXX005). Note these files are symlinks to files hosted on the work disk to reduce the overall storage size of the repo.

Each bin contains the following:
* **1** `anglesOmegaPiAmplitude.root` pseudo-data file, containing the $b_1$ and $\rho$ contributions and their angular information
* **1** `anglesOmegaPiPhaseSpace.root` generated phasespace file. Since this is pseudo-data, no detector effects are included so this flat phasespace file is used for both the "generated" and "accepted" files.
* **25** indexed `omegapi_#.fit` files in a `rand` subdirectory, that each contain the AmpTools fit results for a randomized fit to the pseudo-data
* **1** `best.fit` file, that is the best AmpTools fit result (lowest $-2\ln \mathcal{L}$) out of the 25 random fits