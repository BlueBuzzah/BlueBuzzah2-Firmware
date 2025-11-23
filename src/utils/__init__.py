"""
Utils Module
============
Common utility functions and classes for BlueBuzzah v2.

This module provides reusable utilities for:
- Validation helpers for common operations

All utilities are CircuitPython-compatible and avoid standard library
dependencies that aren't available in the CircuitPython environment.

Modules:
    validation: Common validation functions for pins, voltages, etc.

Example:
    from utils.validation import validate_range
    from core.constants import DEVICE_TAG

    print(f"{DEVICE_TAG} Starting application")

    if validate_range(amplitude, 0, 100):
        print(f"{DEVICE_TAG} Valid amplitude")

Module: utils
Version: 2.0.0
"""

from utils.validation import (
    validate_range,
    validate_voltage,
    validate_pin,
    validate_i2c_address
)

__all__ = [
    # Validation
    "validate_range",
    "validate_voltage",
    "validate_pin",
    "validate_i2c_address",
]

__version__ = "2.0.0"
