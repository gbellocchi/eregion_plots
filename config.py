# Copyright 2025 University of Modena and Reggio Emilia.
# Licensed under the Apache License, Version 2.0, see LICENSE for details.
# SPDX-License-Identifier: Apache-2.0
#
# Author: Gianluca Bellocchi <gianluca.bellocchi@unimore.it>

import json
import yaml
from pathlib import Path

from .plotter import SUPPORTED_PLOTS

class ChartConfig:
    def __init__(self, plot_type, config_path):
        self.config = None
        self.plot_type = plot_type
        self.path = config_path
        self.required_keys = {
            "kiviat": ["chart", "fonts", "padding", "legend", "y_axis", "output"],
            "line": ["chart", "fonts", "legend", "y_axis", "output"],
            "bar": ["chart", "fonts", "legend", "y_axis", "output"]
        }

    def load(self):
        if self.plot_type not in SUPPORTED_PLOTS:
            raise ValueError(f"Unsupported plot type '{self.plot_type}'. Available: {SUPPORTED_PLOTS}")
        if self.path and Path(self.path).exists():
            config_file = Path(self.path)
            suffix = config_file.suffix.lower()
            try:
                with open(self.path, 'r', encoding='utf-8') as f:
                    if suffix in ['.yaml', '.yml']:
                        custom_configs = yaml.safe_load(f)
                    else:
                        raise ValueError(f"Unsupported config file format: {suffix}. Use .yaml or .yml")   
                if self.plot_type in custom_configs:
                    self.config = custom_configs[self.plot_type]  
            except (json.JSONDecodeError, yaml.YAMLError) as e:
                raise ValueError(f"Error parsing config file {self.path}: {e}") 
        else:
            raise ValueError(f"❌ Config error: File {self.path} not found")

    def validate(self):
        if(self.config is None):
            raise ValueError(f"❌ Config error: File {self.path} not found")
        missing = [key for key in self.required_keys[self.plot_type] if key not in self.config]
        if missing:
            raise ValueError(f"Missing config sections: {missing}")
        return True

    def log_status(self):
        print(f"📋 [{self.__class__.__name__}] Configuration Summary:")
        print(f"   Plot type: {self.plot_type}")
        print(f"   Config source: {self.path if self.path else 'defaults'}")
        print(f"   Figure size: {self.config['chart']['figure_size']}")
        print(f"   Max score: {self.config['chart']['max_score']}")
        print(f"   Output: {self.config['output']['filename']}.{self.config['output']['format']}")