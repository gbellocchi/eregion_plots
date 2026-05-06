# Copyright 2026 University of Modena and Reggio Emilia.
# Licensed under the Apache License, Version 2.0, see LICENSE for details.
# SPDX-License-Identifier: Apache-2.0
#
# Author: Gianluca Bellocchi <gianluca.bellocchi@unimore.it>

class PulpColors:
    palette = {
        "cores":        (0xA8, 0x33, 0x2C),
        "peripherals":  (0x90, 0x05, 0x68),
        "interconnect": (0x16, 0x87, 0x39),
        "memory":       (0x12, 0x69, 0xB0),
        "accelerators": (0xF2, 0x95, 0x45),
    }

    def get(self, name):
        return self.palette[name]

    def shade_hex(self, name, idx, total, shade_min=0.25, shade_max=1.0):
        # Return hex color string for palette entry *name*
        base = self.palette[name]
        # Apply shading based on index and total number of entries, with a minimum and maximum shade
        shade = shade_max if total == 1 else shade_min + (shade_max - shade_min) * idx / (total - 1)
        # Return the shaded color as a hex string
        return '#{:02x}{:02x}{:02x}'.format(*[int(c * shade + 255 * (1 - shade)) for c in base])