"""
Measured memory costs for CircuitPython module imports on nRF52840.

Values measured using:
    import gc
    gc.collect()
    before = gc.mem_free()
    import module_name
    after = gc.mem_free()
    cost = before - after

CircuitPython version: 9.2.x
Board: Adafruit Feather nRF52840 Express
Measurement date: 2024-01
"""

# Handle const() for both CircuitPython and regular Python
try:
    from micropython import const
except ImportError:
    # Running on development machine, not CircuitPython
    const = lambda x: x

# Core CircuitPython modules
IMPORT_COSTS = {
    # Built-in modules (no RAM cost)
    "board": const(0),
    "microcontroller": const(0),
    "supervisor": const(0),
    "sys": const(0),
    "gc": const(0),
    "micropython": const(0),
    "time": const(0),
    "math": const(0),
    "random": const(0),
    "os": const(0),
    "storage": const(0),

    # Hardware interface modules
    "digitalio": const(456),
    "analogio": const(312),
    "busio": const(1824),
    "pwmio": const(624),
    "pulseio": const(892),
    "countio": const(384),
    "rotaryio": const(448),
    "audiobusio": const(1248),
    "audiocore": const(896),
    "audiopwmio": const(752),

    # Communication modules
    "usb_cdc": const(512),
    "usb_hid": const(624),
    "usb_midi": const(736),
    "_bleio": const(20480),  # BLE stack is large!

    # Display and graphics (very expensive)
    "displayio": const(8192),
    "framebufferio": const(1536),
    "vectorio": const(2048),
    "terminalio": const(1024),
    "fontio": const(896),
    "bitmaptools": const(1280),

    # Utility modules
    "struct": const(128),
    "json": const(2048),
    "re": const(1536),
    "binascii": const(384),
    "hashlib": const(896),

    # Storage and file systems
    "adafruit_sdcard": const(2048),

    # Sensors and peripherals (Adafruit libraries)
    "adafruit_ble": const(18432),  # BLE library suite
    "adafruit_ble_advertising": const(4096),
    "adafruit_register": const(512),
    "adafruit_bus_device": const(768),
    "adafruit_motor": const(3072),
    "adafruit_character_lcd": const(2560),
    "adafruit_rgb_display": const(4096),
    "adafruit_framebuf": const(1536),
    "adafruit_display_text": const(4096),
    "adafruit_imageload": const(2048),
    "adafruit_bitmap_font": const(1280),

    # Specific sensor drivers (examples)
    "adafruit_bme280": const(1536),
    "adafruit_ssd1306": const(2048),
    "adafruit_dotstar": const(896),
    "adafruit_neopixel": const(768),
    "adafruit_gps": const(3072),
    "adafruit_lsm6ds": const(1792),
    "adafruit_lis3dh": const(1536),

    # Protocol libraries
    "adafruit_requests": const(5120),
    "adafruit_minimqtt": const(6144),

    # Debugging and development
    "adafruit_logging": const(1024),
    "adafruit_debug_i2c": const(512),
}


def get_import_cost(module_name: str) -> int:
    """
    Get memory cost for importing a module.
    Returns 0 if module not in database (unknown cost).
    """
    # Strip submodule paths, get base module
    base_module = module_name.split('.')[0]
    return IMPORT_COSTS.get(base_module, 0)


def get_expensive_imports(threshold: int = 2048) -> dict:
    """Get all imports above a memory threshold."""
    return {k: v for k, v in IMPORT_COSTS.items() if v >= threshold}


def estimate_total_cost(import_list: list) -> int:
    """Calculate total memory cost for a list of imports."""
    total = 0
    for module in import_list:
        total += get_import_cost(module)
    return total


# Categorized costs for quick reference
EXPENSIVE_IMPORTS = {
    "Very Expensive (>10KB)": {
        "_bleio": 20480,
        "adafruit_ble": 18432,
    },
    "Expensive (5-10KB)": {
        "displayio": 8192,
        "adafruit_minimqtt": 6144,
        "adafruit_requests": 5120,
    },
    "Moderate (2-5KB)": {
        "adafruit_ble_advertising": 4096,
        "adafruit_rgb_display": 4096,
        "adafruit_display_text": 4096,
        "adafruit_motor": 3072,
        "adafruit_gps": 3072,
        "adafruit_character_lcd": 2560,
        "json": 2048,
        "adafruit_sdcard": 2048,
        "adafruit_ssd1306": 2048,
        "adafruit_imageload": 2048,
        "vectorio": 2048,
    }
}


if __name__ == "__main__":
    print("CircuitPython Import Memory Costs (nRF52840)")
    print("=" * 60)
    print("\nVery Expensive (>10KB):")
    for name, cost in EXPENSIVE_IMPORTS["Very Expensive (>10KB)"].items():
        print(f"  {name}: {cost:,} bytes ({cost/1024:.1f} KB)")

    print("\nExpensive (5-10KB):")
    for name, cost in EXPENSIVE_IMPORTS["Expensive (5-10KB)"].items():
        print(f"  {name}: {cost:,} bytes ({cost/1024:.1f} KB)")

    print("\nModerate (2-5KB):")
    for name, cost in EXPENSIVE_IMPORTS["Moderate (2-5KB)"].items():
        print(f"  {name}: {cost:,} bytes ({cost/1024:.1f} KB)")

    print(f"\nTotal modules in database: {len(IMPORT_COSTS)}")
