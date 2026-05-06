# Copyright 2025 University of Modena and Reggio Emilia.
# Licensed under the Apache License, Version 2.0, see LICENSE for details.
# SPDX-License-Identifier: Apache-2.0
#
# Author: Gianluca Bellocchi <gianluca.bellocchi@unimore.it>

import matplotlib.pyplot as plt
from matplotlib import font_manager
from math import pi
import itertools
import numpy as np
import os

class KiviatPlotter:
    def __init__(self, data, config):
        self.data = data
        self.config = config
        self.category_groups = None
        self.fig = None
        self.ax = None
    
    def plot(self):
        """Create the Kiviat chart"""
        
        # Extract config sections
        curves_config = self.config["curves"]
        chart_config = self.config["chart"]
        font_config = self.config["fonts"] 
        padding_config = self.config["padding"]
        legend_config = self.config["legend"]
        y_axis_config = self.config.get("y_axis", {})

        # Get number of X categories
        first_df = next(iter(self.data.values()))
        x_categories = first_df.index.values
        N = len(x_categories)

        # Calculate angles for X categories
        angles = [n / float(N) * 2 * pi for n in range(N)]
        angles += angles[:1]

        # Create figure
        self.fig, self.ax = plt.subplots(figsize=tuple(chart_config["figure_size"]), subplot_kw=dict(polar=True))

        # Configure plot style
        self._configure_plot_style(chart_config)

        # Plot category backgrounds
        self._plot_category_backgrounds(x_categories, angles, chart_config)
        
        # Set up axes
        self._setup_axes(chart_config, font_config, padding_config, y_axis_config, angles, x_categories)
        
        # Plot data
        self._plot_curves(curves_config, chart_config, angles)
        
        # Add legend
        self._add_legend(legend_config, font_config)
        
        return self.fig, self.ax

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
            filename = output_config.get("filename", "kiviat")
        
        file_format = output_config.get("format", "pdf")
        full_filename = os.path.join(output_folder, f"{filename}.{file_format}")
        
        self.fig.savefig(
            full_filename,
            dpi=output_config.get("dpi", 300),
            format=file_format,
            transparent=output_config.get("transparent", False),
            bbox_inches=output_config.get("bbox_inches", "tight")
        )
        
        print(f"✅ [{self.__class__.__name__}] Chart saved as {full_filename}")
        return full_filename
    
    def _plot_category_backgrounds(self, x_categories, angles, chart_config):
        """Plot the background for category groups"""
        if self.category_groups and len(self.category_groups) > 1:
            N = len(x_categories)
            step = 2 * np.pi / N

            group_colors = {
                "Platform": "#EEEEEE",
                "Toolchain": "#EEEEEE",
                "Exploration": "#EEEEEE"
            }

            for group, cats in self.category_groups.items():
                idxs = [x_categories.index(cat) for cat in cats]
                start_angle = angles[min(idxs)]
                width = step * len(idxs)
                self.ax.bar(
                    x=start_angle + width/2,
                    height=chart_config["max_score"] + 20,
                    width=width,
                    bottom=0,
                    color=group_colors.get(group, "#EEEEEE"),
                    alpha=0.25,
                    align='center',
                    zorder=0,
                    edgecolor=None
                )

    def _configure_plot_style(self, chart_config):
        """Configure the visual style of the plot"""
        self.ax.set_theta_offset(pi / 2)
        self.ax.set_theta_direction(-1)
        self.ax.spines['polar'].set_visible(True)
        self.ax.spines['polar'].set_linewidth(chart_config["line_width_external_grid"])
        self.ax.grid(True, linestyle='-', linewidth=chart_config["line_width_inner_grid"], color='black')

    def _setup_axes(self, chart_config, font_config, padding_config, y_axis_config, angles, x_categories):
        """Setup chart axes"""
        
        # Wrap labels
        categories_wrapped = self._wrap_labels(x_categories, padding_config["max_label_length"])
        
        # Set tick labels
        plt.xticks(angles[:-1], categories_wrapped, color='black', 
                  size=font_config["category_size"])
        
        # Set padding
        padding_fracs = padding_config["default_category_padding"]
        padding_list = [frac * chart_config["max_score"] for frac in padding_fracs]
        self._set_category_padding(self.ax, angles, categories_wrapped, 
                           padding_list, chart_config, font_config)
        
        # Y-axis configuration
        y_tick_values = y_axis_config.get("tick_values")
        y_tick_labels = y_axis_config.get("tick_labels")
        y_tick_horizontal_padding_factor = y_axis_config.get("tick_horizontal_padding_factor")
        y_tick_vertical_padding_factor = y_axis_config.get("tick_vertical_padding_factor")
        y_tick_is_plot_last = y_axis_config.get("tick_is_plot_last")
        
        # Get angular offset for Y-axis labels only (to avoid overlap with data markers)
        y_axis_angular_offset = y_axis_config.get("angular_offset", 0)  # In radians
        
        # Place Y-axis labels between grid lines to avoid marker overlap
        if y_tick_values and y_tick_labels:
            # Create offset positions - configurable placement between tick values
            offset_positions = []

            for i in range(len(y_tick_values) - 1):
                # Get offset factor from config (default to 0.5 for halfway)
                offset_factor = y_axis_config.get("label_offset_factor", y_tick_vertical_padding_factor[i])
            
                # Flexible label positioning based on offset_factor:
                # 0.0 = at current tick, 0.5 = halfway, 1.0 = at next tick
                # You can also use values outside [0,1] for creative positioning
                offset_pos = y_tick_values[i] + offset_factor * (y_tick_values[i + 1] - y_tick_values[i])
                offset_positions.append(offset_pos)
            
            # Set grid lines at original positions (for visual reference)
            self.ax.set_rticks(y_tick_values)
            self.ax.set_yticklabels([])  # Hide original radial tick labels
            
            # Apply angular offset to Y-axis labels only (not the chart data)
            y_axis_angle = y_axis_angular_offset  # Radial displacement for Y-axis labels
            horizontal_padding = y_tick_horizontal_padding_factor  # Constant horizontal distance from Y-axis line
            
            for pos, label in zip(offset_positions, y_tick_labels[:-1]):  # Use all labels except last
                # Calculate angle needed for consistent horizontal offset at the displaced position
                label_angle = y_axis_angle + np.arcsin(horizontal_padding / pos) if pos > horizontal_padding else y_axis_angle + 0.05
                
                self.ax.text(label_angle, pos, label,
                           ha='center', va='center',
                           color=y_axis_config.get("tick_color", "black"),
                           fontsize=y_axis_config.get("tick_size", 10))
            
            # Add the last label if there are enough tick values
            if len(y_tick_labels) > len(offset_positions) and y_tick_is_plot_last is True:
                # Get the offset factor for the last label (same as other labels)
                last_interval_idx = len(y_tick_values) - 1  # Index for the last interval
                if last_interval_idx < len(y_tick_vertical_padding_factor):
                    last_offset_factor = y_tick_vertical_padding_factor[last_interval_idx]
                else:
                    last_offset_factor = y_axis_config.get("label_offset_factor", 0.5)
                
                # Calculate the last label position using the same offset logic as other labels
                last_interval = y_tick_values[-1] - y_tick_values[-2] if len(y_tick_values) > 1 else 1
                last_pos = y_tick_values[-1] + last_offset_factor * last_interval
                
                # Calculate angle for consistent horizontal offset for last label
                label_angle = y_axis_angle + np.arcsin(horizontal_padding / last_pos) if last_pos > horizontal_padding else y_axis_angle + 0.05
                
                self.ax.text(label_angle, last_pos, y_tick_labels[-1],
                           ha='center', va='center',
                           color=y_axis_config.get("tick_color", "black"),
                           fontsize=y_axis_config.get("tick_size", 10))
        else:
            # Fallback to default behavior if no tick configuration
            self.ax.set_rlabel_position(0)
            plt.yticks(y_tick_values or [], y_tick_labels or [],
                      color=y_axis_config.get("tick_color", "black"),
                      size=y_axis_config.get("tick_size", 10))
        
        plt.ylim(0, chart_config["max_score"])
        # Set padding factor for Y-axis (>=1)
        padding_factor = 1
        # Set Y-axis limits with padding
        self.ax.set_ylim(0, chart_config["max_score"] * padding_factor) 

        if hasattr(self, 'category_groups') and self.category_groups and len(self.category_groups) > 1:
            for group, cats in self.category_groups.items():
                idxs = [x_categories.index(cat) for cat in cats]
                angles_group = [angles[i] for i in idxs]
                mean_angle = np.mean(angles_group)
                category_padding = 1.3
                self.ax.text(
                    mean_angle,
                    chart_config["max_score"] * 1.3,  # Place further out than category labels
                    group,
                    ha='center', va='center',
                    fontsize=font_config.get("category_size", 12) + 2,
                    fontweight='bold',
                    color='dimgray'
                )

    def _set_category_padding(self, ax, angles, categories_wrapped, padding_list, chart_config, font_config):
        """Set custom padding space in between the category labels and Kiviat chart"""
        # Remove default tick labels
        ax.set_xticklabels([])
        
        # Manually place each label with custom padding
        for i, (angle, label, pad) in enumerate(zip(angles[:-1], categories_wrapped, padding_list)):
            # Calculate position with custom padding
            x = angle
            radius = chart_config["max_score"] + pad  # Base radius + custom padding

            # Set alignment of text labels (text boxes) based on their angular position in the chart
            
            # Convert angle to account for theta_offset and theta_direction
            theta_corrected = angle * ax.get_theta_direction() + ax.get_theta_offset()
            theta_corrected = pi/2 - theta_corrected
            
            # Calculate [x,y] components to determine alignment
            y_component = np.cos(theta_corrected) 
            x_component = np.sin(theta_corrected)
            
            # Determine anchor points (the tick of the text box) based on their angular position in the
            # chart quadrant: this ensures the correct edge/corner of the text box is used as reference
            
            # Determine quadrant and set appropriate anchor point
            if x_component >= 0.1 and y_component >= 0.1:
                # Top-right quadrant: anchor at bottom-left of text box
                ha, va = 'left', 'bottom'
            elif x_component <= -0.1 and y_component >= 0.1:
                # Top-left quadrant: anchor at bottom-right of text box
                ha, va = 'right', 'bottom'
            elif x_component <= -0.1 and y_component <= -0.1:
                # Bottom-left quadrant: anchor at top-right of text box
                ha, va = 'right', 'top'
            elif x_component >= 0.1 and y_component <= -0.1:
                # Bottom-right quadrant: anchor at top-left of text box
                ha, va = 'left', 'top'
            elif x_component >= 0.1:
                # Right side: anchor at left edge of text box
                ha, va = 'left', 'center'
            elif x_component <= -0.1:
                # Left side: anchor at right edge of text box
                ha, va = 'right', 'center'
            elif y_component >= 0.5:
                # Top side: anchor at bottom edge of text box
                ha, va = 'center', 'bottom'
            elif y_component <= -0.5:
                # Bottom side: anchor at top edge of text box
                ha, va = 'center', 'top'
            else:
                # Center: use center anchor
                ha, va = 'center', 'center'

            font_props = font_manager.FontProperties(
                size=font_config.get("category_size", 12), 
                weight=font_config.get("weight", "bold")
            )
            
            # Use the label as-is since LaTeX formatting is already in the YAML config
            # The LaTeX rendering will handle the formatting commands
            label_formatted = label
                    
            # Place text at calculated position with angle-based alignment
            ax.text(x, radius, label_formatted, rotation=0, ha=ha, va=va, 
                color='black', fontproperties=font_props)

    def _wrap_labels(self, labels, max_length=10):
        """Wrap long category names"""
        wrapped = []
        for label in labels:
            if len(label) > max_length and ' ' in label:
                # Split at space if longer than max_length
                wrapped.append(label.replace(' ', '\n'))
            else:
                wrapped.append(label)
        return wrapped

    def _plot_curves(self, curves_config, chart_config, angles):
        """Plot the actual data"""
        
        # Get marker and line configuration
        line_width = chart_config.get("line_width_chart", 2)
        marker_sizes = chart_config.get("marker_sizes", [10] * len(self.data))
        marker_edge_widths = chart_config.get("marker_edge_widths", [0.5] * len(self.data))
        fill_alpha = chart_config.get("fill_alpha", 0.1)
        
        # Create iterators for cycling through configurations
        curves_cycle = itertools.cycle(curves_config)
        marker_sizes_cycle = itertools.cycle(marker_sizes)
        marker_edge_widths_cycle = itertools.cycle(marker_edge_widths)
        
        # Plot each curve
        for name, df in self.data.items():
            print(f"🎨 [{self.__class__.__name__}] Plotting kiviat: {name}")

            # Get plot elements
            curve = next(curves_cycle)
            marker_size = next(marker_sizes_cycle)
            marker_edge_width = next(marker_edge_widths_cycle)

            # Get style parameters
            color = curve.get("color")
            transparency = curve.get("transp", 1.0)
            line = curve.get("line_style")
            marker = curve.get("marker")
            
            # Get all y columns (all columns in the dataframe)
            y_columns = df.columns.tolist()

            # Iterate over y columns
            for y_col in y_columns:
                y = df[y_col].values.tolist()
                
                # Close the polygon for Kiviat (add first value at the end)
                values = y + y[:1]
                
                # Generate label name
                yname = name if len(y_columns) == 1 else f"{name}-{y_col}"
                
                # Create plot
                self.ax.plot(
                    angles, 
                    values,
                    color=color,
                    alpha=transparency,
                    linewidth=line_width, 
                    linestyle=line, 
                    marker=marker, 
                    markersize=marker_size,
                    markerfacecolor=color,
                    markeredgecolor='black', 
                    markeredgewidth=marker_edge_width,
                    label=yname,
                    clip_on=False,
                    zorder=100  # Ensure markers are drawn on top
                )
                
                # Fill the area (Kiviat-specific)
                self.ax.fill(angles, values, color=color, alpha=fill_alpha)

    def _add_legend(self, legend_config, font_config):
        """Add legend to the plot"""
        legend = plt.legend(
            title=legend_config["title"],
            title_fontsize=font_config["legend_title_size"],
            fontsize=font_config["legend_size"],
            loc=legend_config["location"], 
            bbox_to_anchor=tuple(legend_config["bbox_anchor"]),
            frameon=legend_config["frameon"]
        )
        legend._legend_box.align = "left"