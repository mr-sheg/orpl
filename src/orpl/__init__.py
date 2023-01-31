"""
ORPL
================
the Open Raman Processing Library is a collection of tools for the processing, analysis and
visualization of Raman spectrum.
"""

from orpl import (
    baseline_removal,
    calibration,
    cosmic_ray,
    metrics,
    normalization,
    plot,
    synthetic,
)

if __name__ == "__main__":
    from orpl.GUI.orplGUI import launch_gui

    launch_gui()
