"""Python batch script version of the interactive tutorial notebook

This script will obtain the data and best fit files, convert them to csv, and then
plot the results. The plots will be saved in the analysis directory. Note that many of 
explanations and comments are in the tutorial notebook, and this is intended to be
an example of how to run the analysis in more of a batch mode.

NOTE: make sure to source setup_gluex.(c)sh before running this script
"""

import subprocess
import sys
from pathlib import Path

import matplotlib
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

# add parent directory to system path to import analysis script
parent_dir = str(Path(__file__).resolve().parents[1])
sys.path.insert(0, parent_dir)
import analysis.utils as utils

# Suppress matplotlib from outputting any graphics
matplotlib.use("Agg")

# Obtain the data files and produce "data.csv"
data_proc = subprocess.Popen(
    (
        f"python {parent_dir}/scripts/convert_to_csv.py -i"
        f" {parent_dir}/data/*/*Amplitude.root"
        f" -o {parent_dir}/analysis/data.csv"
    ),
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE,
    text=True,
    shell=True,
)
stdout, stderr = data_proc.communicate()
if data_proc.returncode != 0:
    print(f"Error: {stderr}")
else:
    print(stdout)

# Obtain the best fit files and produce "best_fits.csv"
data_proc = subprocess.Popen(
    (
        f"python {parent_dir}/scripts/convert_to_csv.py -i"
        f" {parent_dir}/data/*/*best.fit"
        f" -o {parent_dir}/analysis/best_fits.csv"
    ),
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE,
    text=True,
    shell=True,
)
stdout, stderr = data_proc.communicate()
if data_proc.returncode != 0:
    print(f"Error: {stderr}")
else:
    print(stdout)

# load files
df_fit = pd.read_csv(f"{parent_dir}/analysis/best_fits.csv")
df_data = pd.read_csv(f"{parent_dir}/analysis/data.csv")

if df_fit.shape[0] != df_data.shape[0]:
    raise ValueError("Data and fit results don't have the same number of bins")

# wrap phases to be in the range (-180, 180]
utils.wrap_phases(df_fit)

# change matplotlib settings for all plots
matplotlib.rcParams.update(
    {
        "figure.figsize": (10, 8),
        "figure.dpi": 100,
        "xtick.labelsize": 14,
        "ytick.labelsize": 14,
        "axes.labelsize": 16,
        "legend.fontsize": 16,
        "xtick.major.width": 2.0,
        "ytick.major.width": 2.0,
        "xtick.minor.width": 1.8,
        "ytick.minor.width": 1.8,
        "lines.markersize": 10,
        "grid.alpha": 0.8,
        "axes.grid": True,
    }
)
plt.minorticks_on()
plt.close()  # suppress outputting an empty plot

# define some common plot parameters
mass_bins = df_data["m_center"]
bin_width = (df_data["m_high"] - df_data["m_low"])[0]  # just use 1st bin width entry
coherent_sums = utils.get_coherent_sums(df_fit)
phase_differences = utils.get_phase_differences(df_fit)

# --- PLOT JP VALUES ---

# I prefer this colormap over the default
jp_colors = matplotlib.colormaps["Dark2"].colors
fig, ax = plt.subplots()

# plot data as black dots
ax.errorbar(
    x=mass_bins,
    y=df_data["events"],
    xerr=bin_width / 2.0,
    yerr=df_data["events_err"],
    fmt="k.",
    label="Signal MC",
)

# Plot Fit Result as a grey histogram with its error bars
ax.bar(
    x=mass_bins,
    height=df_fit["detected_events"],
    width=bin_width,
    color="0.1",
    alpha=0.15,
    label="Fit Result",
)
ax.errorbar(
    x=mass_bins,
    y=df_fit["detected_events"],
    yerr=df_fit["detected_events_err"],
    fmt=",",
    color="0.1",
    alpha=0.2,
    markersize=0,
)

# plot 1+
ax.errorbar(
    x=mass_bins,
    y=df_fit["1p"],
    xerr=bin_width / 2.0,
    yerr=df_fit["1p_err"],
    label=utils.convert_amp_name(
        "1p"
    ),  # converts amplitude / phase differences to be in J^P L_m^(e) format
    linestyle="",  # want only markers, no lines\
    marker="1",
    color=jp_colors[2],
)

# plot 1-
ax.errorbar(
    x=mass_bins,
    y=df_fit["1m"],
    xerr=bin_width / 2.0,
    yerr=df_fit["1m_err"],
    label=utils.convert_amp_name(
        "1m"
    ),  # converts amplitude / phase differences to be in J^P L_m^(e) format
    linestyle="",  # want only markers, no lines\
    marker="s",
    color=jp_colors[3],
)

ax.set_xlabel(r"$\omega\pi^0$ inv. mass $(GeV)$", loc="right")
ax.set_ylabel(f"Events / {bin_width:.3f} GeV", loc="top")
ax.set_ylim(bottom=0.0)
ax.legend()
plt.savefig(f"{parent_dir}/analysis/jp_plot.png")
plt.close()

# --- PLOT INDIVIDUAL WAVES ---
# define some dictionaries to convert characters <-> integers
char_to_int = {"m": -1, "0": 0, "p": +1, "S": 0, "P": 1, "D": 2}
int_to_char = {-1: "m", 0: "0", +1: "p"}
pm_dict = {"m": "-", "p": "+"}

# sort the JPL values by the order of S, P, D, F waves, and the m-projections
jpl_values = sorted(coherent_sums["JPL"], key=lambda JPL: char_to_int[JPL[-1]])
m_ints = sorted({char_to_int[JPmL[-2]] for JPmL in coherent_sums["JPmL"]})

fig, axs = plt.subplots(
    nrows=len(jpl_values),
    ncols=len(m_ints),
    sharex=True,
    # sharey=True, # uncomment to compare relative intensities
    figsize=(15, 10),
)

# iterate through JPL (sorted like S, P, D, F wave) and sorted m-projections
for row, jpl in enumerate(jpl_values):
    for col, m in enumerate(m_ints):

        # force sci notation so large ticklabels don't overlap with neighboring plots
        axs[row, col].ticklabel_format(axis="y", style="sci", scilimits=(0, 0))

        # recombine jpl and m to get string needed to access the column
        JPmL = f"{jpl[0:2]}{int_to_char[m]}{jpl[-1]}"

        # set the labels for the first rows and columns
        if row == 0:
            axs[row, col].set_title(f"m={m}", fontsize=18)
        if col == 0:
            J = JPmL[0]
            P = pm_dict[JPmL[1]]
            L = JPmL[-1]
            axs[row, col].set_ylabel(rf"${J}^{{{P}}}{L}$", fontsize=18)

        # plot the negative reflectivity contribution
        neg_plot = axs[row, col].errorbar(
            x=mass_bins,
            y=df_fit[f"m{JPmL}"],
            xerr=bin_width / 2.0,
            yerr=df_fit[f"m{JPmL}_err"],
            marker="v",
            linestyle="",
            markersize=8,
            color="blue",
            alpha=0.5,  # prevent overlap from cluttering the view
            label=r"$\varepsilon=-1$",
        )
        # plot the positive reflectivity contribution
        pos_plot = axs[row, col].errorbar(
            x=mass_bins,
            y=df_fit[f"p{JPmL}"],
            xerr=bin_width / 2.0,
            yerr=df_fit[f"p{JPmL}_err"],
            marker="^",
            linestyle="",
            markersize=8,
            color="red",
            alpha=0.5,
            label=r"$\varepsilon=+1$",
        )

# reset limits to 0 for all plots
for ax in axs.reshape(-1):
    ax.set_ylim(bottom=0)

# figure cosmetics
fig.text(0.5, 0.04, r"$\omega\pi^0$ inv. mass (GeV)", ha="center", fontsize=20)
fig.text(
    0.04,
    0.5,
    f"Events / {bin_width:.3f} GeV",
    ha="center",
    va="center",
    rotation="vertical",
    rotation_mode="anchor",
    fontsize=20,
)

# the pos/neg_plot variables get overwritten in the loop, so we're only passing one set
# of handles to the figure, which is okay since all plots have the same legend. If we
# didn't do this, every single plots redundant legend would be displayed
fig.legend(handles=[pos_plot, neg_plot], loc="upper right")
plt.savefig(f"{parent_dir}/analysis/individual_waves.png")
plt.close()

# --- PLOT PHASE DIFFERENCE OF MAJOR WAVE ---

fig, axs = plt.subplots(
    2, 1, sharex=True, gridspec_kw={"wspace": 0.0, "hspace": 0.07}, height_ratios=[3, 1]
)

amp1, amp2 = "p1p0S", "p1mpP"

# plot the first amplitude
axs[0].errorbar(
    x=mass_bins,
    y=df_fit[amp1],
    xerr=bin_width / 2.0,
    yerr=df_fit[f"{amp1}_err"],
    marker="o",
    linestyle="",
    color="green",
    label=utils.convert_amp_name(amp1),
)
# plot the second amplitude
axs[0].errorbar(
    x=mass_bins,
    y=df_fit[amp2],
    xerr=bin_width / 2.0,
    yerr=df_fit[f"{amp2}_err"],
    marker="s",
    linestyle="",
    color="purple",
    label=utils.convert_amp_name(amp2),
)

# plot the phase difference. Since there is an inherent ambiguity in the sign of the
# phase difference within the model, we need to plot both signs to accommodate for every
# possible phase motion
phase_dif = phase_differences[(amp1, amp2)]
axs[1].errorbar(
    x=mass_bins,
    y=df_fit[phase_dif],
    xerr=bin_width / 2.0,
    yerr=df_fit[f"{phase_dif}_err"].abs(),
    marker=".",
    linestyle="",
    color="black",
)
axs[1].errorbar(
    x=mass_bins,
    y=-df_fit[phase_dif],
    xerr=bin_width / 2.0,
    yerr=df_fit[f"{phase_dif}_err"].abs(),
    marker=".",
    linestyle="",
    color="black",
)

# cosmetics
axs[0].set_ylim(bottom=0.0)
axs[0].set_ylabel(f"Events / {bin_width:.3f} GeV", loc="top")

axs[1].set_yticks(np.linspace(-180, 180, 5))  # force to be in pi intervals
axs[1].set_ylim([-180, 180])
axs[1].set_ylabel(r"Phase Diff. ($^{\circ}$)", loc="center")
axs[1].set_xlabel(r"$\omega\pi^0$ inv. mass $(GeV)$", loc="right")

axs[0].legend(loc="upper left")

plt.savefig(f"{parent_dir}/analysis/wave_and_phase_motion.png")
plt.close()
