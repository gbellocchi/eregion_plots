# Copyright 2025 University of Modena and Reggio Emilia.
# Licensed under the Apache License, Version 2.0, see LICENSE for details.
# SPDX-License-Identifier: Apache-2.0
#
# Author: Gianluca Bellocchi <gianluca.bellocchi@unimore.it>

import matplotlib.pyplot as plt
import os
import itertools

linestyle_std = {
    'solid': 'solid',      # Same as (0, ()) or '-'
    'dotted': 'dotted',    # Same as ':'
    'dashed': 'dashed',    # Same as '--'
    'dashdot': 'dashdot'   # Same as '-.'
}

linestyle_extra = {
    'loosely dotted':        (0, (1, 10)),
    'dotted':                (0, (1, 5)),
    'densely dotted':        (0, (1, 1)),
    'long dash with offset': (5, (10, 3)),
    'loosely dashed':        (0, (5, 10)),
    'dashed':                (0, (5, 5)),
    'densely dashed':        (0, (5, 1)),
    'loosely dashdotted':    (0, (3, 10, 1, 10)),
    'dashdotted':            (0, (3, 5, 1, 5)),
    'densely dashdotted':    (0, (3, 1, 1, 1)),
    'dashdotdotted':         (0, (3, 5, 1, 5, 1, 5)),
    'loosely dashdotdotted': (0, (3, 10, 1, 10, 1, 10)),
    'densely dashdotdotted': (0, (3, 1, 1, 1, 1, 1))
}

class LinePlotter:
    def __init__(self, data, config):
        self.data = data
        self.config = config
        self.fig = None
        self.ax = None

    def plot(self):
        """Create the Line chart"""
        
        # Extract config sections
        curves_config = self.config["curves"]
        chart_config = self.config["chart"]
        font_config = self.config["fonts"]
        legend_config = self.config["legend"]
        x_axis_config = self.config.get("x_axis", {})
        y_axis_config = self.config.get("y_axis", {})

        # Create figure
        self.fig, self.ax = plt.subplots(figsize=tuple(chart_config["figure_size"]))

        # Set up axes
        self._setup_axes(chart_config, font_config, x_axis_config, y_axis_config)

        # Plot data
        self._plot_curves(curves_config, chart_config)

        # Add curve note boxes (annotations)
        self._add_curve_note_box(font_config)

        # Add legend
        self._add_legend(legend_config, chart_config, font_config)

    def save(self, filename=None, filepath=None):
        """Save the plot"""
        if self.fig is None:
            raise ValueError("No plot to save. Call plot() first.")

        script_dir = os.path.dirname(os.path.abspath(__file__))
        output_folder = os.path.join(script_dir, filepath)
        if not os.path.isdir(output_folder):
            raise FileNotFoundError(f"Output folder '{output_folder}' does not exist. Please create it before saving.")

        output_config = self.config.get("output", {})
        if filename is None:
            filename = output_config.get("filename", "line")

        file_format = output_config.get("format", "pdf")
        full_filename = os.path.join(output_folder, f"{filename}.{file_format}")

        self.fig.savefig(
            full_filename,
            dpi=output_config.get("dpi", 300),
            transparent=output_config.get("transparent", False),
            bbox_inches=output_config.get("bbox_inches", "tight")
        )

        print(f"✅ [{self.__class__.__name__}] Chart saved as {full_filename}")
        return full_filename
    
    def _setup_axes(self, chart_config, font_config, x_axis_config, y_axis_config):
        """Setup chart axes"""
        # X-axis configuration
        self.ax.set_xlabel(chart_config.get("xlabel", ""), fontsize=font_config.get("label_size", 12))

        # Set X-axis scale (linear or logarithmic)
        if x_axis_config.get("log_scale", False):
            self.ax.set_xscale('log', base = x_axis_config.get("log_base", 10))
        
        # Set X-axis ticks
        if x_axis_config.get("equidistant", False):
            if "tick_values" in x_axis_config:
                # Create equidistant positions (0, 1, 2, ...)
                tick_positions = list(range(len(x_axis_config["tick_values"])))
                self.ax.set_xticks(tick_positions)
                # Use tick_labels if provided, otherwise fall back to tick_values
                if "tick_labels" in x_axis_config:
                    labels_to_use = x_axis_config["tick_labels"]
                else:
                    labels_to_use = x_axis_config["tick_values"]
                
                self.ax.set_xticklabels(
                    labels_to_use, 
                    fontsize=x_axis_config.get("tick_size", 12),
                    rotation=x_axis_config.get("tick_rotation", 0)
                )
                # Store mapping for plotting (you'll need this in _plot_curves)
                self.x_value_mapping = {val: pos for pos, val in enumerate(x_axis_config["tick_values"])}
            else:
                print("Warning: equidistant=True requires 'tick_values' to be specified")
        else:
            # Normal behavior
            if "tick_values" in x_axis_config:
                self.ax.set_xticks(x_axis_config["tick_values"])
            if "tick_labels" in x_axis_config:
                self.ax.set_xticklabels(
                    x_axis_config["tick_labels"],
                    fontsize=x_axis_config.get("tick_size", 12),
                    rotation=x_axis_config.get("tick_rotation", 0)
                )

        # Set X-axis limits
        if "xlim" in x_axis_config:
            xlim = x_axis_config["xlim"]
            # Check if explicit padding is requested
            if "padding_absolute" in x_axis_config:
                # Absolute padding (fixed units)
                padding = x_axis_config["padding_absolute"]
                xlim = [xlim[0] - padding, xlim[1] + padding]
            self.ax.set_xlim(xlim)
        
        # Add X-axis padding (margins) to ensure markers are visible
        x_padding = x_axis_config.get("padding", 0.05)  # Default 5% padding
        if x_padding > 0:
            self.ax.margins(x=x_padding)

        # Y-axis configuration
        self.ax.set_ylabel(chart_config.get("ylabel", ""), fontsize=font_config.get("label_size", 12))

        # Set Y-axis scale (linear or logarithmic)
        if y_axis_config.get("log_scale", False):
            self.ax.set_yscale('log', base = y_axis_config.get("log_base", 10))

        # Set Y-axis ticks
        if "tick_values" in y_axis_config:
            self.ax.set_yticks(y_axis_config["tick_values"])
        if "tick_labels" in y_axis_config:
            self.ax.set_yticklabels(y_axis_config["tick_labels"], fontsize=font_config.get("tick_size", 10))

        # Set Y-axis limits with optional padding
        if "ylim" in y_axis_config:
            ylim = y_axis_config["ylim"]
            # Check if explicit padding is requested
            if "padding_absolute" in y_axis_config:
                # Absolute padding (fixed units)
                padding = y_axis_config["padding_absolute"]
                ylim = [ylim[0] - padding, ylim[1] + padding]
            self.ax.set_ylim(ylim)
        
        # Add Y-axis padding (margins) to ensure markers are visible
        y_padding = y_axis_config.get("padding", 0.05)  # Default 5% padding
        if y_padding > 0:
            self.ax.margins(y=y_padding)

        # Title and grid
        self.ax.set_title(chart_config.get("title", ""), fontsize=font_config.get("title_size", 14))
        self.ax.grid(chart_config.get("grid", True))

    def _plot_curves(self, curves_config, chart_config):
        """Plot the actual data"""

        marker_sizes = chart_config.get("marker_sizes", [10] * len(self.data))
        marker_edge_widths = chart_config.get("marker_edge_widths", [10] * len(self.data))

        curves_cycle = itertools.cycle(curves_config)
        marker_sizes_cycle = itertools.cycle(marker_sizes)
        marker_edge_widths_cycle = itertools.cycle(marker_edge_widths)

        # Plot each curve
        for name, df in self.data.items():
            print(f"🎨 [{self.__class__.__name__}] Plotting curve: {name}")

            # Get plot elements
            curve = next(curves_cycle)
            marker_size = next(marker_sizes_cycle)
            marker_edge_width = next(marker_edge_widths_cycle)

            # Get style parameters
            color = curve.get("color")
            transparency = curve.get("transp")
            line = curve.get("line_style")
            marker = curve.get("marker")
            markevery = curve.get("markevery", None)
            zorder = curve.get("zorder", 100)

            # Get x values
            x_orig = df.index.values

            # Transform x values if equidistant spacing is enabled
            if hasattr(self, 'x_value_mapping'):
                # Map original x values to equidistant positions
                x_plot = [self.x_value_mapping.get(val, val) for val in x_orig]
            else:
                x_plot = x_orig
                
            # Get all y columns (all columns except 'x')
            y_columns = df.columns.tolist()

            # Iterate over y columns
            for y_col in y_columns:
                y = df[y_col].values
                
                # Generate label name
                yname = name if len(y_columns) == 1 else f"{name}-{y_col}"
                
                # Create plot
                self.ax.plot(
                    x_plot,
                    y,
                    color=color,
                    alpha=transparency,
                    linewidth=chart_config.get("line_width_chart", 2),
                    linestyle=line,
                    marker=marker,
                    markevery=markevery,
                    markerfacecolor=color,
                    markersize=marker_size,
                    markeredgecolor='black', 
                    markeredgewidth=marker_edge_width,
                    label=yname,
                    zorder=zorder,  # Ensure markers are drawn on top
                    clip_on=False  # Prevent clipping of markers at plot boundaries
                )

    def _add_legend(self, legend_config, chart_config, font_config):
        if chart_config.get("legend", True):
            """Add legend to the plot"""
            handles, labels = self.ax.get_legend_handles_labels()
            handle_order = legend_config.get("handle_order", list(range(len(handles))))
            bbox_anchor = legend_config.get("bbox_anchor")
            bbox_anchor_offset = legend_config.get("bbox_anchor_offset")
            if bbox_anchor_offset is not None:
                loc = legend_config.get("location", "best")
                xo, yo = bbox_anchor_offset
                x = (1 - xo) if "right" in loc else (xo if "left" in loc else 0.5)
                y = (1 - yo) if "upper" in loc else (yo if "lower" in loc else 0.5)
                bbox_anchor = [x, y]
            legend = plt.legend(
                [handles[i] for i in handle_order],
                [labels[i] for i in handle_order],
                title=legend_config["title"],
                title_fontsize=font_config["legend_title_size"],
                fontsize=font_config["legend_size"],
                loc=legend_config["location"],
                borderaxespad=legend_config.get("borderaxespad", 0.5),
                **({"bbox_to_anchor": tuple(bbox_anchor)} if bbox_anchor is not None else {}),
                frameon=legend_config["frameon"],
                ncol=legend_config["ncol"],
                fancybox=False, 
                shadow=True,
                labelspacing=legend_config.get("labelspacing", 0.5),
                handlelength=legend_config.get("handlelength", 2.0),
                handletextpad=legend_config.get("handletextpad", 0.8),
                borderpad=legend_config.get("borderpad", 0.4),
                columnspacing=legend_config.get("columnspacing", 2.0),
            )
            legend._legend_box.align = "center"
            # Set legend frame color to black
            legend.get_frame().set_edgecolor('black')

    def _add_curve_note_box(self, font_config):
        """Add text boxes for curve annotations"""
        text_box_config = self.config.get("text_boxes", {})
        if text_box_config.get("enabled", False):
            self.text_boxes = []
            for box_config in text_box_config.get("boxes", []):
                # Create text box
                bbox_props = dict(
                    boxstyle=box_config.get("boxstyle", "round,pad=0.3"),
                    facecolor=box_config.get("facecolor", "white"),
                    edgecolor=box_config.get("edgecolor", "black"),
                    alpha=box_config.get("alpha", 0.8),
                    linewidth=box_config.get("linewidth", 1)
                )
                
                text_box = self.ax.text(
                    box_config.get("x", 0.5),
                    box_config.get("y", 0.5),
                    box_config.get("text", ""),
                    transform=self.ax.transAxes if box_config.get("use_relative_coords", True) else self.ax.transData,
                    fontsize=box_config.get("fontsize", font_config.get("tick_size", 10)),
                    ha=box_config.get("ha", "center"),  # 'left', 'center', 'right'
                    va=box_config.get("va", "center"),  # 'top', 'center', 'bottom'
                    rotation=box_config.get("rotation", 0),  # Rotation angle in degrees
                    rotation_mode=box_config.get("rotation_mode", "default"),  # 'default' or 'anchor'
                    bbox=bbox_props,
                    zorder=box_config.get("zorder", 10)
                )
                self.text_boxes.append(text_box)