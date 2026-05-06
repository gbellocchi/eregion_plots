# Copyright 2025 University of Modena and Reggio Emilia.
# Licensed under the Apache License, Version 2.0, see LICENSE for details.
# SPDX-License-Identifier: Apache-2.0
#
# Author: Gianluca Bellocchi <gianluca.bellocchi@unimore.it>

import pandas as pd
import numpy as np
from scipy.interpolate import interp1d, make_interp_spline
import os
from tabulate import tabulate

class Dataset:
    def __init__(self, config_curves, config_dir, datasets_path, x_common=None):
        # Chart configuration
        self.config_curves = config_curves
        self.config_dir = config_dir
        self.datasets_path = datasets_path
        if not config_curves:
            raise ValueError("No curves configuration provided")
        # Initialize x values and check whether they are shared among all curves values or private
        if x_common is not None:
            self.x_common = x_common
        else:
            self.x_common = []
        self.x_private = []
        self.y_private = []
        # Header row
        self.header = []
        # Initialize generic dataset populated while processing the chart configuration
        self.datasets = {}
        # Initialize pandas dataframe compatible data structure
        self.pd_dataframe = {}

    def process_config(self):
        """Process curves from input configuration"""
        # Process each chart
        for chart in self.config_curves:
            # Get chart name
            if "name" not in chart:
                raise ValueError("Each chart must have a 'name' field")
            else:
                chart_name = chart["name"]
            # Get chart values
            if "values" not in chart:
                raise ValueError("Each chart must have a 'values' field")
            else:
                chart_values = chart["values"]

            # Check if values are stored in a file (`file`) or are specified in the .yml descriptor (`x_private`, `y_private`)
            self.is_x_common = 0 # if x_common is defined
            self.is_x_private = 0 # if is_x_private is defined
            self.is_y_private = 0 # if is_y_private is defined
            self.is_x_from_file = 0 # if x is loaded from a file
            self.is_y_from_file = 0 # if y is loaded from a file
            
            # Check if x_common
            if len(self.x_common) > 0:
                self.is_x_common = 1
                if isinstance(self.x_common, str):
                    self.x = float(self.x_common)
                else:
                    self.x = self.x_common
            # Check if x_private
            if chart_values["x_private"]:
                self.is_x_private = 1
                if isinstance(chart_values["x_private"], str):
                    self.x = float(chart_values["x_private"])
                else:
                    self.x = chart_values["x_private"]
            # Check if x is loaded from a file
            if not (self.is_x_common or self.is_x_private):
                filename = chart_values["file"]
                if isinstance(filename, str):
                    if '.' in filename and (filename.endswith(('.txt', '.csv', '.dat', '.json'))):
                        self.is_x_from_file = 1
                    else:
                        raise ValueError(f"String value '{filename}' doesn't appear to be a valid filename with supported extension")

            # Check if y_private
            if chart_values["y_private"]:
                self.is_y_private = 1
                if isinstance(chart_values["y_private"], str):
                    self.y = float(chart_values["y_private"])
                else:
                    self.y = chart_values["y_private"]
            # Check if y is loaded from a file
            if not self.is_y_private:
                filename = chart_values["file"]
                if isinstance(filename, str):
                    if '.' in filename and (filename.endswith(('.txt', '.csv', '.dat', '.json'))):
                        self.is_y_from_file = 1
                    else:
                        raise ValueError(f"String value '{filename}' doesn't appear to be a valid filename with supported extension")
                    
            # Load x-y values from file
            if self.is_x_from_file or self.is_y_from_file:
                self._load_from_file(os.path.join(self.datasets_path, chart_values["file"]))
            
            # At this stage, self.x and self.y should be populated
            if not self.x and not self.y:
                raise ValueError("No x-y dataset is present")
            elif(self.x and not isinstance(self.x, list)) or (self.y and not isinstance(self.y, list)):
                raise ValueError("Invalid data format: x-y must be lists")
            elif(self.x and isinstance(self.x, list)) or (self.y and isinstance(self.y, list)):
                print(f"✅ [{self.__class__.__name__}] Dataset lists detected")

            # Store the processed dataset
            dataset = {
                "x": self.x,
                "y": self.y
            }
            self.datasets[chart_name] = dataset

    def convert_to_pd_dataframe(self):
        """Convert to Pandas dataframe"""
        for name in self.datasets:
            # Convert to DataFrame
            print(f"📄 [{self.__class__.__name__}] Converting dataset '{name}' to pandas DataFrame")
            # Create empty dictionary to temporarily hold data
            dataset = {}
            # Organize dataset into dictionary
            # The first column (x) will be the dataframe index
            for d in range(len(self.datasets[name]["y"])):
                # If a header is present, use it for column naming
                if self.header and len(self.header) > 1:
                    # d+1 because header[0] is for x (index)
                    dataset[f"{self.header[d+1]}"] = self.datasets[name]["y"][d]
                # Else use y0, y1, etc.
                else:
                    dataset[f"y{d}"] = self.datasets[name]["y"][d]
            # Create DataFrame with x as index
            if self.header and len(self.header) > 1:
                df = pd.DataFrame(dataset, index=self.datasets[name]["x"], columns=self.header[1:])
            else:
                df = pd.DataFrame(dataset, index=self.datasets[name]["x"], columns=['y'+str(i) for i in range(len(self.datasets[name]["y"]))])
            self.pd_dataframe[name] = df

    def print_pd_dataframes(self, tablefmt='grid'):
        print("\n" + "="*80)
        print("📊 PANDAS DATAFRAMES CONTENT")
        print("="*80)
        
        for name, df in self.pd_dataframe.items():
            print(f"\n📄 DataFrame: {name}")
            print(tabulate(df, headers='keys', tablefmt=tablefmt, showindex=True))
            print(f"\nShape: {df.shape[0]} rows × {df.shape[1]} columns")
        
        print("\n" + "="*80 + "\n")

    def interpolate(self, num_points=300, method='cubic'):
        """Interpolate dataset points from pandas dataframe"""
        for name in self.pd_dataframe:
            df = self.pd_dataframe[name]
            # Get original x values
            x_orig = df['x'].values
            # Create new x range for interpolation
            x_new = pd.Series(range(int(x_orig.min()), int(x_orig.max()) + 1, max(1, (int(x_orig.max()) - int(x_orig.min())) // num_points)))
            
            # Interpolate each y dimension
            interpolated_data = {'x': x_new}
            for col in df.columns:
                if col.startswith('y'):
                    y_orig = df[col].values
                    # Linear interpolation
                    if method == 'linear':
                        interp_func = interp1d(x_orig, y_orig, kind='linear', 
                        bounds_error=False, fill_value='extrapolate')
                        y_new = interp_func(x_new)
                    # Cubic interpolation
                    elif method == 'cubic':
                        if len(x_orig) > 3:  # Need at least 4 points for cubic
                            spline = make_interp_spline(x_orig, y_orig, k=3)
                            y_new = spline(x_new)
                        else:
                            raise ValueError(f"Not enough points for cubic interpolation in '{name}', {col}. Need at least 4 points, got {len(x_orig)}.")    
                    else:
                        raise ValueError(f"Invalid interpolation method '{method}'.")
                    # Get interpolated data
                    interpolated_data[col] = y_new
            
            # Update the dataframe with interpolated data
            self.pd_dataframe[name] = pd.DataFrame(interpolated_data)
            print(f"🔄 [{self.__class__.__name__}] Interpolated dataset '{name}' with {len(x_new)} points using {method} method")

    def _load_from_file(self, filepath):
        """Supports:
        - Multi-dimensional data (x, y1, y2, etc.) 
        - Each dimension is separated by comma, space, or tab
        - Each set of dimensions (y1, y2, etc. sampled at different x values) is separated by newline
        - Assumption: x is supposed to be the same for each dimension
        """
        try:
            with open(filepath, 'r') as f:
                filevals = f.read().strip()

            # Extract values from file into list of strings
            rows = [v.strip() for v in filevals.split('\n') if v.strip()]
            if not rows:
                return []
        
            # Determine type of separator between multi-dimensional data
            first_row_str = rows[0]
            separator = self._detect_separator(first_row_str)

            # Determine number of dimensions
            first_row_list = [x.strip() for x in first_row_str.split(separator) if x.strip()]       
            self.n_x_dim = 1 # Assumption: x is supposed to be the same for each dimension
            # If file includes x values then one column is for x
            if(self.is_x_from_file):
                self.n_y_dim = len(first_row_list) - 1
            # If file only includes y values, then each column is a separate y dimension
            else:
                self.n_y_dim = len(first_row_list)
            print(f"📊 [{self.__class__.__name__}] Detected {self.n_x_dim} x dimensions in data file: {filepath}")
            print(f"📊 [{self.__class__.__name__}] Detected {self.n_y_dim} y dimensions in data file: {filepath}")

            # Populate dataset lists
            x = [] # independent variables
            y = [] # dependent variables, potentially multi-dim (n_y_dim > 1), such as: [[y-dim1, y-dim2, ...], [...]]

            # Read each row
            for row_str in rows:
                row_split = [r.strip() for r in row_str.split(separator) if r.strip()]
                if len(row_split) < len(first_row_list):
                    print(f"⚠️ [{self.__class__.__name__}] Warning: Row has fewer columns than expected: {row_str}")
                    continue

                # Check if this row contains header strings or numeric values
                is_header = self._is_header_row(row_split)
                
                # Skip header rows and only process numeric data
                if is_header:
                    continue

                # If x values are not read from file
                if not self.is_x_from_file:
                    # x_private or x_common are already assigned then
                    pass
                # If x values are provided with y values in a file
                else: 
                    # The first element of each row corresponds to the independent variable
                    try:
                        x.append(float(row_split[0]))
                    except ValueError:
                        x.append(row_split[0])
                        print(f"ℹ️ [{self.__class__.__name__}] Using categorical x value: '{row_split[0]}'")

                # If y values are not read from file
                if not self.is_y_from_file:
                    # y_private are already assigned then
                    pass
                # If y values are not provided with x values in a file
                elif not self.is_x_from_file: 
                    # row_split only comprises dependent variables, each corresponding to a different dimension
                    y_values = [float(val) for val in row_split[0:]]
                    y.append(y_values)
                # If y values are provided with x values in a file
                else:
                    # Others are dependent variables, each corresponding to a different dimension
                    y_values = [float(val) for val in row_split[1:]]
                    y.append(y_values)
                
            # Flatten into separated y list for each dimension
            # From [[y-dim1, y-dim2, ...], [...]] to [[y-dim1], [y-dim2], ...]
            if y:  # Only process if we have data
                y_flat = [[] for _ in range(self.n_y_dim)]
                for y_dim_list in y:
                    for d in range(min(len(y_dim_list), self.n_y_dim)):
                        y_flat[d].append(y_dim_list[d])
            else:
                y_flat = [[] for _ in range(self.n_y_dim)] 

            # Populate dataset lists      
            self.x = x
            self.y = y_flat
        except FileNotFoundError:
            print(f"❌ [{self.__class__.__name__}] Warning: File {filepath} not found. Using empty values.")
            return []
        except ValueError as e:
            print(f"❌ [{self.__class__.__name__}] Warning: Error parsing values from {filepath}: {e}")
            return []
        
    def _detect_separator(self, sample_string):
        # Separators to check (in order)
        # N.B.: space is treated separately at the end
        separators = [
            ',', 
            ';',
            '|',
            '\t',
            ':'
        ]
        
        for separator in separators:
            if separator in sample_string:
                parts = sample_string.split(separator)
                # Check consistency, i.e., if we get at least 2 substrings with content
                valid_parts = [p.strip() for p in parts if p.strip()]
                if len(valid_parts) < 2:
                    continue

                # Check if spaces are consistently at the beginning of parts (after separator)
                spaces_at_start = 0
                spaces_at_end = 0

                for i, part in enumerate(parts):
                    # Skip empty parts and first/last parts (edge cases)
                    if not part.strip():
                        continue
                    if i > 0 and part.startswith(' '):
                        spaces_at_start += 1
                    if i < len(parts) - 1 and part.endswith(' '):
                        spaces_at_end += 1

                # Determine the final separator with spaces
                final_separator = separator
                
                # If most parts have leading spaces, include space after separator
                if spaces_at_start >= len(valid_parts) - 1:
                    final_separator = separator + ' '
                # If most parts have trailing spaces, include space before separator
                elif spaces_at_end >= len(valid_parts) - 1:
                    final_separator = ' ' + separator
                
                return final_separator
        
        # Check for space as separator (if nothing else matched)
        parts = sample_string.split(' ')
        valid_parts = [p.strip() for p in parts if p.strip()]
        if len(valid_parts) >= 2:
            return ' '
        
        # Default fallback
        return ' '
    
    def _is_header_row(self, row_split):
        # Check if all values in a row are strings (non-numeric)
        all_strings = True
        for val in row_split:
            try:
                float(val)
                all_strings = False
                break
            except ValueError:
                continue
        
        # If not all strings, it's not a header
        if not all_strings:
            return False
        
        self.header = row_split
        
        # If all values are strings (non-numeric), it's a header
        return True