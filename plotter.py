# Copyright 2025 University of Modena and Reggio Emilia.
# Licensed under the Apache License, Version 2.0, see LICENSE for details.
# SPDX-License-Identifier: Apache-2.0
#
# Author: Gianluca Bellocchi <gianluca.bellocchi@unimore.it>

import matplotlib.pyplot as plt

from .kiviat import KiviatPlotter
from .line import LinePlotter
from .bar import BarPlotter

SUPPORTED_PLOTS = {
    "kiviat": {
        "class": "KiviatPlotter",
        "implemented": True,
        "description": "Radar chart"
    },
    "line": {
        "class": "LinePlotter",
        "implemented": True,
        "description": "Line chart"
    },
    "bar": {
        "class": "BarPlotter",
        "implemented": True,
        "description": "Bar chart"
    }
}

# Render text with LaTeX
# Note: When using LaTeX rendering, font variants like 'small-caps' in FontProperties 
# are ignored. Use LaTeX commands like \textsc{} instead.
# For Times New Roman with small caps support, we need to use LaTeX fonts
plt.rcParams.update({
    "text.usetex": True,
    "font.family": "serif",
    "font.serif": ["Times"],
    "text.latex.preamble": r"\usepackage{times}", 
})
    
def create_plotter(plot_type, data, config):
    """Simple factory for different plot types"""
    if plot_type == "kiviat":
        return KiviatPlotter(data, config)
    elif plot_type == "line":
        return LinePlotter(data, config)
    elif plot_type == "bar":
        return BarPlotter(data, config)
    else:
        available = ["kiviat", "line", "bar"]
        raise ValueError(f"No plotter for '{plot_type}'. Available: {available}")
    
def get_supported_plots():
    """Get list of implemented plot types"""
    return [plot for plot, info in SUPPORTED_PLOTS.items() if info["implemented"]]