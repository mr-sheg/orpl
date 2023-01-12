"""
Bubblegif is a module used for the generation of gifs that show how the bubblefill algorithm works.
"""
import os
import shutil

import numpy as np
import matplotlib.pyplot as plt
from scipy.signal import savgol_filter
from PIL import Image

from orpl.baseline_removal import grow_bubble, keep_largest

GIFDIR = "gif"
FONTSIZE = 9
fig = plt.figure()


def savefig(figname=None):
    """
    savefig saves the figure in the 'gif/' directory

    Parameters
    ----------
    figname : _type_, optional
        _description_, by default None
    """
    # get number of files in GIFDIR
    if figname:
        plt.savefig(os.path.join(GIFDIR, figname))
    else:
        nfile = len(os.listdir(GIFDIR))
        plt.savefig(os.path.join(GIFDIR, f"{nfile}.png"))


def plotstep0(spectrum: np.ndarray):
    """
    plotstep0 plots bubblefill step 0 -> input spectrum

    Parameters
    ----------
    spectrum : np.ndarray
        The bubblefill input spectrum
    """
    fig.clear()
    plt.plot(spectrum)
    plt.xlabel("Detector pixel (0 to N)")
    plt.ylabel("Intensity [counts]")
    plt.title("Step 0 : Input Spectrum")
    plt.tight_layout()

    # saving figure
    savefig("step_0.png")


def plotstep1(spectrum: np.ndarray, polyfit: np.ndarray, spectrum_: np.ndarray):
    """
    plotstep1 plots bubblefill step 1 -> after global slope removal

    Parameters
    ----------
    spectrum : np.ndarray
        The spectrum after global slope removal
    """
    fig.clear()
    plt.plot(spectrum, label="$S_0$ : Input Spectrum")
    plt.plot(polyfit, label="$P_0$ : linear slope fit", zorder=0)
    plt.plot(spectrum_, label="$S_0 - P_0$", zorder=0)
    plt.xlabel("Detector pixel (0 to N)")
    plt.ylabel("Intensity [counts]")
    plt.title("Step 1 : Global slope removal")
    plt.legend(fontsize=FONTSIZE, framealpha=1)
    plt.tight_layout()

    # saving figure
    savefig("step_1.png")


def plotstep2(spectrum: np.ndarray):
    """
    plotstep2 plots bubblefill step 2 -> normalization to square aspect ratio

    Parameters
    ----------
    spectrum : np.ndarray
        The normalized spectrum
    """

    fig.clear()
    plt.plot(spectrum)
    plt.xlabel("Detector pixel (0 to N)")
    plt.ylabel("Normalized intensity (0 to N) [au]")
    plt.title("Step 2 : Normalization to square aspect ratio")
    plt.tight_layout()

    savefig("step_2.png")


def plotstep3(spectrum: np.ndarray, baseline: np.ndarray):
    """
    plotstep3 plots bubblefill step 3 -> initial baseline fit

    Parameters
    ----------
    spectrum : np.ndarray
        Normalized spectrum
    baseline : np.ndarray
        initial baseline fit (vector of 0)
    """
    fig.clear()
    plt.plot(spectrum, label="Normalized spectrum", zorder=1)
    plt.plot(baseline, label="Initial baseline fit", zorder=0, color="tab:orange")
    plt.xlabel("Detector pixel (0 to N)")
    plt.ylabel("Normalized intensity (0 to N) [au]")
    plt.title("Step 3 : Baseline fit initialization")
    plt.legend(fontsize=FONTSIZE, framealpha=1)
    plt.tight_layout()

    savefig("step_3.png")


def plotbubbleupdate(
    i,
    spectrum: np.ndarray,
    baseline: np.ndarray,
    bubble: np.ndarray,
    touching_point: int,
    left_bound: int,
    right_bound: int,
    min_bubble_widths: list,
):
    """
    plotbubbleupdate Plots the bubblefill bubble growth loop.

    Parameters
    ----------
    i : _type_
        the number of the current loop itteration
    spectrum : np.ndarray
        the normalized spectrum
    baseline : np.ndarray
        the current baseline fit (of that loop)
    bubble : np.ndarray
        the bubble grown during that itteration
    touching_point : int
        the xaxis location where the bubble made contact
    left_bound : int
        the left bound of the bubble (xaxis position)
    right_bound : int
        the right bound of the bubble (xaxis position)
    min_bubble_widths : list
        the smallest allowed bubble width (exit parameter)
    """
    fig.clear()
    plt.plot(spectrum, label="Normalized spectrum", zorder=10)
    plt.plot(baseline, label="Baseline fit", color="tab:orange", zorder=0)
    plt.plot(
        touching_point,
        spectrum[touching_point],
        "x",
        label="Point of contact",
        color="tab:red",
        zorder=11,
    )
    plt.plot(
        range(left_bound, right_bound),
        bubble,
        label=f"Bubble {i}",
        color="tab:red",
        zorder=5,
    )

    # adding smallest bubble
    theta = np.linspace(0, 2 * np.pi, 100)
    if min_bubble_widths is not int:
        radius = max(min_bubble_widths) / 2
    else:
        radius = min_bubble_widths / 2
    a = radius * np.cos(theta)
    a = a - a.min()
    b = radius * np.sin(theta)
    b = max(spectrum) - b - b.max()
    plt.plot(a, b, color="tab:green", label="Smallest allowed bubble")

    plt.legend(loc="upper right", fontsize=FONTSIZE, framealpha=1)
    plt.ylim([-0.05 * max(spectrum), 1.05 * max(spectrum)])
    plt.xlabel("Detector pixel (0 to N)")
    plt.ylabel("Normalized intensity (0 to N) [au]")
    plt.title(f"Step 4 : Bubble growth loop (i={i})")
    plt.tight_layout()

    savefig(figname=f"loop_{i}.png")


def plotstep4(spectrum: np.ndarray, baseline: np.ndarray):
    """
    plotstep4 plots bubblefill results after bubble growth loop

    Parameters
    ----------
    spectrum : _type_
        spectrum
    baseline : _type_
        baseline fit after bubble growth is complete
    """
    fig.clear()
    plt.plot(spectrum, label="Normalized spectrum")
    plt.plot(baseline, label="Baseline fit", color="tab:orange")

    plt.legend(loc="upper right", fontsize=FONTSIZE, framealpha=1)
    plt.ylim([-0.05 * max(spectrum), 1.05 * max(spectrum)])
    plt.xlabel("Detector pixel (0 to N)")
    plt.ylabel("Normalized intensity (0 to N) [au]")
    plt.title(f"Step 4 : Baseline fit after bubble growth process")

    plt.tight_layout()

    savefig("step_4.png")


def plotstep5(spectrum, baseline):
    """
    plotstep5 plots bubblefill step 5, reversing normalization and square aspect ratio

    Parameters
    ----------
    spectrum : np.ndarray
        de-normalized spectrum
    basleine : np.ndarray
        de-normalized baseline
    """
    fig.clear()
    plt.plot(spectrum, label="Input spectrum")
    plt.plot(baseline, label="Baseline fit", color="tab:orange")

    plt.legend(loc="upper right", fontsize=FONTSIZE, framealpha=1)
    plt.ylim([-0.05 * max(spectrum), 1.05 * max(spectrum)])
    plt.xlabel("Detector pixel (0 to N)")
    plt.ylabel("Intensity [counts]")
    plt.title(f"Step 5 : Reversion of normalization and scaling")

    plt.tight_layout()

    savefig("step_5.png")


def plotstep6(spectrum: np.ndarray, baseline: np.ndarray):
    """
    plotstep6 plots bubblefill step 6, savgol filter for smoothing baseline

    Parameters
    ----------
    spectrum : np.ndarray
        input spectrum
    baseline : np.ndarray
        final baseline fit
    """
    fig.clear()
    plt.plot(spectrum, label="Input spectrum")
    plt.plot(baseline, label="Final baseline fit", color="tab:orange")

    plt.legend(loc="upper right", fontsize=FONTSIZE, framealpha=1)
    plt.ylim([-0.05 * max(spectrum), 1.05 * max(spectrum)])
    plt.xlabel("Detector pixel (0 to N)")
    plt.ylabel("Intensity [counts]")
    plt.title(f"Step 6 : smoothing of baseline fit with Savitzky-Golay filter")

    plt.tight_layout()

    savefig("step_6.png")


def plotstep7(spectrum: np.ndarray, baseline: np.ndarray, raman: np.ndarray):
    """
    plotstep7 plots bubblefill step 7, final baseline removal and raman spectrum

    Parameters
    ----------
    spectrum : np.ndarray
        input spectrum
    baseline : np.ndarray
        final baseline fit
    raman : np.ndarray
        computed raman spectrum
    """
    fig.clear()
    plt.plot(spectrum, label="Input spectrum")
    plt.plot(baseline, label="Final baseline fit", color="tab:orange")
    plt.plot(raman, label="Final raman", color="tab:green")

    plt.legend(loc="upper right", fontsize=FONTSIZE, framealpha=1)
    plt.ylim([-0.05 * max(spectrum), 1.05 * max(spectrum)])
    plt.xlabel("Detector pixel (0 to N)")
    plt.ylabel("Intensity [counts]")
    plt.title("Step 7 : Final Raman and baseline")

    plt.tight_layout()

    savefig("step_7.png")


def bubbleloop(
    spectrum: np.ndarray, baseline: np.ndarray, min_bubble_widths: list
) -> np.ndarray:
    """
    bubbleloop itteratively updates a baseline estimate by growing bubbles under a spectrum.

    Usage
    -----
    baseline = bubbleloop(spectrum, baseline, min_bubble_widths)

    Parameters
    ----------
    spectrum : np.ndarray
        the input spectrum
    baseline : np.ndarray
        the initial baseline should be akin to np.zeros(spectrum.shape)
    min_bubble_widths : list
        the minimum bubble widths to use. Can be an array-like or int.
        if array-like -> must be the same length as spectrum and baseline. Useful to specify
        different bubble sizes based on x-coordinates.
        if int -> will use the same width for all x-coordinates.

    Returns
    -------
    baseline : np.ndarray
        the updated baseline
    """
    # initial range is always 0 -> len(s). aka the whole spectrum
    # bubblecue is a list of bubble x-coordinate span as
    # [[x0, x2]_0, [x0, x2]_1, ... [x0, x2]_n]
    # additional bubble regions are added as the loop runs.
    range_cue = [[0, len(spectrum)]]

    i = 0
    while i < len(range_cue):
        # Bubble parameter from bubblecue
        left_bound, right_bound = range_cue[i]
        i += 1

        if left_bound == right_bound:
            continue

        if isinstance(min_bubble_widths, int):
            min_bubble_width = min_bubble_widths
        else:
            min_bubble_width = min_bubble_widths[(left_bound + right_bound) // 2]

        if left_bound == 0 and right_bound != (len(spectrum)):
            # half bubble right
            alignment = "left"
        elif left_bound != 0 and right_bound == (len(spectrum)):
            alignment = "right"
            # half bubble left
        else:

            # Reached minimum bubble width
            if (right_bound - left_bound) < min_bubble_width:
                continue
            # centered bubble
            alignment = "center"

        # new bubble
        bubble, relative_touching_point = grow_bubble(
            spectrum[left_bound:right_bound], alignment
        )
        touching_point = relative_touching_point + left_bound

        # add bubble to baseline by keeping largest value
        baseline[left_bound:right_bound] = keep_largest(
            baseline[left_bound:right_bound], bubble
        )

        # Plot step
        if i > 0:
            plotbubbleupdate(
                i,
                spectrum,
                baseline,
                bubble,
                touching_point,
                left_bound,
                right_bound,
                min_bubble_widths,
            )

        # Add new bubble(s) to bubblecue
        if touching_point == left_bound:
            range_cue.append([touching_point + 1, right_bound])
        elif touching_point == right_bound:
            range_cue.append([left_bound, touching_point - 1])
        else:
            range_cue.append([left_bound, touching_point])
            range_cue.append([touching_point, right_bound])

    return baseline


def bubblefill(
    spectrum: np.ndarray, min_bubble_widths: list = 50, fit_order: int = 1
) -> (np.ndarray, np.ndarray):
    """
    bubblefill splits a spectrum into it's raman and baseline components.

    Usage
    -----
    raman, baseline = bubblefill(spectrum, bubblewidths, fitorder)

    Parameters
    ----------
    spectrum : np.ndarray
        the input spectrum
    min_bubble_widths: list or int
        is the smallest width allowed for bubbles. Smaller values will
        allow bubbles to penetrate further into peaks resulting
        in a more *aggressive* baseline removal. Larger values are more
        *concervative* and might the computed underestimate baseline.
        use list to specify a minimum width that depends on the
        x-coordinate of the bubble. Make sure len(bubblewidths) = len(spectrum).
        Otherwise if bubblewidths [int], the same width is used for all x-coordinates.
    fit_order : int
        the order of the polynomial fit used to remove the *overall* baseline slope.
        Recommendend value is 1 (for linear slope).
        Higher order will result in Runge's phenomena and
        potentially undesirable and unpredictable effects.
        fitorder = 0 is the same as not removing the overall baseline slope

    Returns
    -------
    raman : np.ndarray
        the spectrum's raman component
    baseline : np.ndarray
        the spectrum's baseline component

    Reference
    ---------
    Guillaume Sheehy 2021-01
    """
    # Setup figure save directory
    if os.path.exists(GIFDIR):
        shutil.rmtree(GIFDIR)
        os.mkdir(GIFDIR)
    else:
        os.mkdir(GIFDIR)

    plotstep0(spectrum)

    xaxis = np.arange(len(spectrum))

    # Remove general slope
    poly_fit = np.poly1d(np.polyfit(xaxis, spectrum, fit_order))(xaxis)
    spectrum_ = spectrum - poly_fit

    plotstep1(spectrum, poly_fit, spectrum_)

    # Normalization
    smin = spectrum_.min()  # value needed to return to the original scaling
    spectrum_ = spectrum_ - smin
    scale = spectrum_.max() / len(spectrum)
    spectrum_ = spectrum_ / scale  # Rescale spectrum to X:Y=1:1 (square aspect ratio)

    plotstep2(spectrum_)

    baseline = np.zeros(spectrum_.shape)

    plotstep3(spectrum_, baseline)

    # Bubble loop (this is the bulk of the algorithm)
    baseline = bubbleloop(spectrum_, baseline, min_bubble_widths)

    plotstep4(spectrum_, baseline)

    # Bringing baseline back in original scale
    baseline = baseline * scale + poly_fit + smin

    plotstep5(spectrum, baseline)

    # Final smoothing of baseline (only if bubblewidth is not a list!!!)
    if isinstance(min_bubble_widths, int):
        baseline = savgol_filter(baseline, 2 * (min_bubble_widths // 4) + 1, 3)

    plotstep6(spectrum, baseline)

    raman = spectrum - baseline

    plotstep7(spectrum, baseline, raman)

    return raman, baseline


def bubblegif(
    spectrum: np.ndarray,
    gif_name: str,
    min_bubble_widths: list = 50,
    fit_order: int = 1,
    gif_duration: int = 20,
    loop_duration_ratio: float = 0.5,
):
    """
    bubblegif bubblegif Generates an animated gif of the bubblefill growth loop process and still frame
    images of the other steps.

    Parameters
    ----------
    spectrum : np.ndarray
        _description_
    gif_name : str
        _description_
    min_bubble_widths : list, optional
        _description_, by default 50
    fit_order : int, optional
        _description_, by default 1
    gif_duration : int, optional
        _description_, by default 10
    loop_duration_ratio : float, optional
        _description_, by default 0.5
    """

    # Create png images
    _, _ = bubblefill(spectrum, min_bubble_widths, fit_order)

    # Creating gif parts
    im_gif_1 = []
    im_gif_2 = []
    im_gif_3 = []
    files = os.listdir("gif")
    files = sorted(files, key=lambda x: int(x.split(".")[0].split("_")[-1]))
    files

    for file in files:
        if file.startswith("loop"):
            im_gif_2.append(Image.open(f"gif/{file}"))
        elif len(im_gif_1) < 4:
            im_gif_1.append(Image.open(f"gif/{file}"))
        else:
            im_gif_3.append(Image.open(f"gif/{file}"))

    long_frame_duration = (
        1000
        * (1 - loop_duration_ratio)
        * gif_duration
        / (len(im_gif_1) + len(im_gif_3))
    )
    quick_frame_duration = 1000 * loop_duration_ratio * gif_duration / len(im_gif_2)

    im_gif_1[0].save(
        f"part1.gif",
        save_all=True,
        append_images=im_gif_1[1:],
        optimize=False,
        duration=long_frame_duration,
    )
    im_gif_2[0].save(
        f"part2.gif",
        save_all=True,
        append_images=im_gif_2[1:],
        optimize=False,
        duration=quick_frame_duration,
    )
    im_gif_3[0].save(
        f"part3.gif",
        save_all=True,
        append_images=im_gif_3[1:],
        optimize=False,
        duration=long_frame_duration,
    )

    # Combining gif parts

    im1 = Image.open("part1.gif")
    im2 = Image.open("part2.gif")
    im3 = Image.open("part3.gif")
    Ims = [im1, im2, im3]

    Ims[0].save(gif_name, save_all=True, append_images=Ims[1:], optimize=True, loop=0)

    # Clean up
    shutil.rmtree("gif")
    for i in range(1, 4):
        os.remove(f"part{i}.gif")
