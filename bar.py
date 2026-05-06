# Copyright 2025 University of Modena and Reggio Emilia.
# Licensed under the Apache License, Version 2.0, see LICENSE for details.
# SPDX-License-Identifier: Apache-2.0
#
# Author: Gianluca Bellocchi <gianluca.bellocchi@unimore.it>

import matplotlib.pyplot as plt
import os
import itertools
import numpy as np

class BarPlotter:
    def __init__(self, data, config):
        self.data = data
        self.config = config
        self.fig = None
        self.ax = None

    def plot(self):
        """Create the Bar chart"""
        
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
        self._plot_bars(curves_config, chart_config)

        # Add legend if enabled
        if legend_config.get("enabled", True): 
            self._add_legend(legend_config, font_config)

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
            filename = output_config.get("filename", "bar")

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

        # Set X-axis ticks
        if "tick_values" in x_axis_config:
            self.ax.set_xticks(x_axis_config["tick_values"])
        if "tick_labels" in x_axis_config:
            self.ax.set_xticklabels(
                x_axis_config["tick_labels"],
                fontsize=x_axis_config.get("tick_size", 12),
                rotation=x_axis_config.get("tick_rotation", 0),
                ha=x_axis_config.get("tick_ha", "center"),  # Horizontal alignment
                va=x_axis_config.get("tick_va", "center")   # Vertical alignment
            )

        # Set X-axis limits
        if "xlim" in x_axis_config:
            self.ax.set_xlim(x_axis_config["xlim"])

        # Y-axis configuration
        self.ax.set_ylabel(chart_config.get("ylabel", ""), fontsize=font_config.get("label_size", 12))

        # Set Y-axis scale (linear or logarithmic)
        if y_axis_config.get("log_scale", False):
            self.ax.set_yscale('log', base=y_axis_config.get("log_base", 10))

        # Set Y-axis ticks
        if "tick_values" in y_axis_config:
            self.ax.set_yticks(y_axis_config["tick_values"])
        if "tick_labels" in y_axis_config:
            self.ax.set_yticklabels(y_axis_config["tick_labels"], fontsize=font_config.get("tick_size", 10))

        # Set Y-axis limits with optional padding
        if "ylim" in y_axis_config:
            ylim = y_axis_config["ylim"]
            if "padding_absolute" in y_axis_config:
                padding = y_axis_config["padding_absolute"]
                ylim = [ylim[0] - padding, ylim[1] + padding]
            self.ax.set_ylim(ylim)

        # Title and grid
        self.ax.set_title(chart_config.get("title", ""), fontsize=font_config.get("title_size", 14))
        self.ax.grid(chart_config.get("grid", True), axis='y')

    def _plot_bars(self, curves_config, chart_config):
        """Plot the actual bar data"""

        # Get bar configuration
        bar_width = chart_config.get("bar_width", 0.8)
        
        num_datasets = len(self.data)
        if num_datasets == 0:
            return
        
        # Determine if this is simple bars (each dataset at its own x position)
        # or grouped bars (multiple datasets at each x position)
        # Simple bars: each dataset has 1 value at a unique x position
        x_positions_list = []
        y_values_list = []
        
        for name, df in self.data.items():
            y_columns = df.columns.tolist()
            y = df[y_columns[0]].values
            y_values_list.append(y)
            
            # Get x positions from dataframe index
            if hasattr(df.index, 'values'):
                x = df.index.values
            else:
                x = np.arange(len(y))
            x_positions_list.append(x)
        
        # Check if this is simple bars: each dataset has exactly 1 value
        is_simple_bars = all(len(y) == 1 for y in y_values_list)
        
        if is_simple_bars:
            # Simple bars - each bar at its own x position
            curves_cycle = itertools.cycle(curves_config)
            
            for idx, (name, df) in enumerate(self.data.items()):
                print(f"🎨 [{self.__class__.__name__}] Plotting bar: {name}")
                
                # Get style parameters
                curve = next(curves_cycle)
                color = curve.get("color", f"C{idx}")
                transparency = curve.get("transp", 1.0)
                edge_color = curve.get("edge_color", "black")
                edge_width = curve.get("edge_width", 1)
                
                x_pos = x_positions_list[idx][0]  # Single x position
                y_val = y_values_list[idx][0]     # Single y value
                
                # Create bar
                self.ax.bar(
                    x_pos,
                    y_val,
                    width=bar_width,
                    color=color,
                    alpha=transparency,
                    edgecolor=edge_color,
                    linewidth=edge_width,
                    label=name,
                    zorder=99
                )
        else:
            # Grouped bars - multiple datasets at shared x positions
            x_axis_config = self.config.get("x_axis", {})
            if "tick_values" in x_axis_config:
                x_positions = np.array(x_axis_config["tick_values"])
            else:
                # Use x positions from first dataset
                x_positions = x_positions_list[0]
            
            num_bars = num_datasets
            total_width = bar_width
            single_bar_width = total_width / num_bars if num_bars > 1 else total_width
            offsets = np.linspace(-total_width/2, total_width/2, num_bars) if num_bars > 1 else [0]
            
            curves_cycle = itertools.cycle(curves_config)
            
            for idx, (name, df) in enumerate(self.data.items()):
                print(f"🎨 [{self.__class__.__name__}] Plotting bar: {name}")
                
                # Get style parameters
                curve = next(curves_cycle)
                color = curve.get("color", f"C{idx}")
                transparency = curve.get("transp", 1.0)
                edge_color = curve.get("edge_color", "black")
                edge_width = curve.get("edge_width", 1)
                
                y = y_values_list[idx]
                
                # Create bars
                self.ax.bar(
                    x_positions + offsets[idx],
                    y,
                    width=single_bar_width,
                    color=color,
                    alpha=transparency,
                    edgecolor=edge_color,
                    linewidth=edge_width,
                    label=name,
                    zorder=99
                )

    def _add_legend(self, legend_config, font_config):
        """Add legend to the plot"""
        legend = plt.legend(
            title=legend_config.get("title", ""),
            title_fontsize=font_config["legend_title_size"],
            fontsize=font_config["legend_size"],
            loc=legend_config["location"], 
            bbox_to_anchor=tuple(legend_config["bbox_anchor"]),
            frameon=legend_config["frameon"],
            ncol=legend_config["ncol"],
            fancybox=False, 
            shadow=True
        )
        legend._legend_box.align = "center"
        legend.get_frame().set_edgecolor('black')
