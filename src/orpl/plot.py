"""
Plot
================

Provides Raman spectrum visualization tools.
"""
import numpy as np
import matplotlib.pyplot as plt


# Spectrum visualization


def shadeplot(spectra: np.ndarray, labels: np.ndarray, xaxis: np.ndarray = None):
    """
    shadeplot [summary]

    Parameters
    ----------
    spectra : np.ndarray
        [description]
    labels : np.ndarray
        [description]
    xaxis : np.ndarray, optional
        [description], by default None
    """
    if xaxis is None:
        xaxis = np.arange(spectra.shape[1])

    for label in np.unique(labels):
        plt.plot(xaxis, spectra[labels == label].mean(axis=0), label=label)
        bottom_line = spectra[labels == label].mean(axis=0) - spectra[
            labels == label
        ].std(axis=0)
        top_line = spectra[labels == label].mean(axis=0) + spectra[labels == label].std(
            axis=0
        )
        plt.fill_between(xaxis, bottom_line, top_line, alpha=0.4)

    plt.legend()


# Hyperspectral visualization


def plot3d(im3d, ijk=None, xaxis=None, color_map="gist_gray"):
    """
    Visualization tool for hyperspectral cubes.

    Usage
    ------
    plot3d(im3d, ijk=None, xaxis=None, color_map='gist_gray')

    Input arguments
    ----------------
    im3d        --> [NDARRAY] a data cube. MUST BE NxMxP

    ijk         --> [list] the starting (i, j, k) coordinate of the cursor

    xaxis       --> [list] a xaxis. MUST BE 1xP

    color_map   --> [string] colormap to use for imshow. MUST BE A VALID
                    matplotlib COLORMAP NAME
    """
    # Default parameters
    if ijk is None:
        ijk = list(np.array(im3d.shape) // 2)

    if xaxis is None:
        xaxis = np.arange(im3d.shape[2])

    # Create figure
    figure = plt.figure(figsize=[10, 5])

    # Setup left axes
    ax1 = plt.subplot(1, 2, 1)
    ax1.set_title(f"ijk = {ijk}")
    im2d = plt.imshow(im3d[:, :, ijk[2]], cmap=color_map)
    im2d.set_autoscale = True

    hline1 = plt.plot([-1, im3d.shape[1]], [ijk[0], ijk[0]], "red")
    vline1 = plt.plot([ijk[1], ijk[1]], [-1, im3d.shape[0]], "red")
    plt.xlim(-0.5, im3d.shape[1] - 0.5)
    plt.ylim(im3d.shape[0] - 0.5, -0.5)

    # Setup right axes
    ax2 = plt.subplot(1, 2, 2)

    line = plt.plot(xaxis, im3d[ijk[0], ijk[1], :])
    vline2 = plt.plot(
        [xaxis[ijk[2]], xaxis[ijk[2]]], [0.9 * im3d.min(), 1.1 * im3d.max()], "red"
    )

    plt.xlim(xaxis.min(), xaxis.max())
    plt.ylim(0.9 * im3d.min(), 1.1 * im3d.max())
    ax2.set_title(f"({int(round(xaxis[ijk[2]]))}, {im3d[ijk[0], ijk[1], ijk[2]]})")

    def update_axis(ijk):
        # Updates left axes
        hline1[0].set_ydata([ijk[0], ijk[0]])
        vline1[0].set_xdata([ijk[1], ijk[1]])
        im2d.set_data(im3d[:, :, ijk[2]])
        im2d.set_norm(None)

        # Updates right axes
        vline2[0].set_xdata([xaxis[ijk[2]], xaxis[ijk[2]]])
        line[0].set_ydata(im3d[ijk[0], ijk[1]])

        # Update titles
        ax1.set_title(f"ijk = {ijk}")
        ax2.set_title(f"({int(round(xaxis[ijk[2]]))}, {im3d[ijk[0], ijk[1], ijk[2]]})")
        figure.canvas.draw()

    # Setup click behavior

    def onclick(event):
        if event.inaxes == ax1:
            ijk[1] = int(event.xdata + 0.5)
            ijk[1] = max(0, min(ijk[1], im3d.shape[1] - 1))
            ijk[0] = int(event.ydata + 0.5)
            ijk[0] = max(0, min(ijk[0], im3d.shape[0] - 1))

            update_axis(ijk)

        elif event.inaxes == ax2:
            ijk[2] = np.abs(xaxis - int(event.xdata + 0.5)).argmin()
            ijk[2] = max(0, min(ijk[2], im3d.shape[2] - 1))

            update_axis(ijk)

    def keypress(event):
        if event.inaxes == ax2:
            if event.key == "up":
                ijk[2] += 1
            elif event.key == "down":
                ijk[2] -= 1
            elif event.key == "left":
                ijk[2] -= 1
            elif event.key == "right":
                ijk[2] += 1
        else:
            if event.key == "up":
                ijk[0] -= 1
            elif event.key == "down":
                ijk[0] += 1
            elif event.key == "left":
                ijk[1] -= 1
            elif event.key == "right":
                ijk[1] += 1

        ijk[0] = max(0, min(ijk[0], im3d.shape[0] - 1))
        ijk[1] = max(0, min(ijk[1], im3d.shape[1] - 1))
        ijk[2] = max(0, min(ijk[2], im3d.shape[2] - 1))

        update_axis(ijk)

    # Link click behavior to figure
    figure.canvas.mpl_connect("button_press_event", onclick)
    figure.canvas.mpl_connect("key_press_event", keypress)
