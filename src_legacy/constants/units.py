"""Unit constants for physical quantities."""

from typing import List

# Common physical units for quick selection in dialogs
COMMON_UNITS: List[str] = [
    "",  # No unit
    # Length
    "m", "cm", "mm", "μm", "nm", "km", "in", "ft",
    # Mass
    "kg", "g", "mg", "μg", "lb", "oz",
    # Time
    "s", "ms", "μs", "ns", "min", "h", "day",
    # Temperature
    "K", "°C", "°F",
    # Pressure
    "Pa", "kPa", "MPa", "bar", "atm", "psi", "mmHg",
    # Volume
    "L", "mL", "μL", "m³", "cm³",
    # Energy
    "J", "kJ", "MJ", "eV", "keV", "MeV", "cal", "kcal",
    # Power
    "W", "kW", "MW", "hp",
    # Electric
    "V", "mV", "A", "mA", "μA", "Ω", "kΩ", "MΩ",
    # Frequency
    "Hz", "kHz", "MHz", "GHz",
    # Angle
    "rad", "deg", "°",
    # Other
    "mol", "%", "ppm", "ppb",
]
