"""
Measure actual memory cost of importing CircuitPython modules.

USAGE:
1. Copy this file to CIRCUITPY drive on nRF52840
2. Modify MODULES_TO_TEST list below
3. Connect to serial REPL
4. Run: import measure_imports
5. Results will show memory cost of each import

This helps populate import_costs.py with accurate measurements
for your specific CircuitPython version and board configuration.
"""

import gc
import sys

# List of modules to measure
# Add any modules you want to test
MODULES_TO_TEST = [
    "board",
    "digitalio",
    "analogio",
    "busio",
    "time",
    "struct",
    "json",
    "_bleio",
    "displayio",
    # Add more modules here
    # "adafruit_ble",
    # "adafruit_motor",
    # etc.
]


def measure_import_cost(module_name):
    """
    Measure memory used by importing a module.
    Returns bytes consumed, or None if import fails.
    """
    # Force garbage collection to get accurate baseline
    gc.collect()
    gc.collect()  # Twice to be thorough

    mem_before = gc.mem_free()

    try:
        # Import the module
        __import__(module_name)

        # Force GC again to account for any temporary allocations
        gc.collect()

        mem_after = gc.mem_free()
        cost = mem_before - mem_after

        return cost

    except ImportError:
        print(f"  [SKIP] Module '{module_name}' not available")
        return None
    except Exception as e:
        print(f"  [ERROR] Failed to import '{module_name}': {e}")
        return None


def measure_all_imports():
    """Measure all modules in MODULES_TO_TEST list."""
    print("\n" + "="*60)
    print("CircuitPython Import Memory Measurement")
    print("="*60)
    print(f"Board: {sys.platform}")
    print(f"CircuitPython version: {sys.version}")
    print("="*60)

    results = {}

    # Measure each module
    for module_name in MODULES_TO_TEST:
        print(f"\nMeasuring: {module_name}...")

        # Need to reload Python to get clean measurement
        # For CircuitPython, we can't really unload modules,
        # so this is a cumulative measurement
        cost = measure_import_cost(module_name)

        if cost is not None:
            results[module_name] = cost
            print(f"  Cost: {cost:,} bytes ({cost/1024:.2f} KB)")

    # Print summary
    print("\n" + "="*60)
    print("Summary - Copy to import_costs.py")
    print("="*60)
    print("\nIMPORT_COSTS = {")

    for module_name in sorted(results.keys()):
        cost = results[module_name]
        print(f'    "{module_name}": const({cost}),')

    print("}")

    total_cost = sum(results.values())
    print(f"\nTotal measured: {total_cost:,} bytes ({total_cost/1024:.2f} KB)")
    print(f"Modules tested: {len(results)}/{len(MODULES_TO_TEST)}")


def measure_single_module(module_name):
    """
    Measure a single module from REPL.

    Usage from REPL:
    >>> import measure_imports
    >>> measure_imports.measure_single_module("adafruit_motor")
    """
    print(f"\nMeasuring '{module_name}'...")

    gc.collect()
    gc.collect()
    mem_before = gc.mem_free()
    print(f"Memory before: {mem_before:,} bytes")

    try:
        __import__(module_name)
        gc.collect()
        mem_after = gc.mem_free()
        cost = mem_before - mem_after

        print(f"Memory after: {mem_after:,} bytes")
        print(f"Import cost: {cost:,} bytes ({cost/1024:.2f} KB)")

        print(f'\nAdd to import_costs.py:')
        print(f'    "{module_name}": const({cost}),')

        return cost

    except ImportError:
        print(f"ERROR: Module '{module_name}' not found")
        return None
    except Exception as e:
        print(f"ERROR: {e}")
        return None


def check_available_memory():
    """Show current memory status."""
    gc.collect()
    gc.collect()

    mem_free = gc.mem_free()
    mem_alloc = gc.mem_alloc()
    total = mem_free + mem_alloc

    print("\n" + "="*60)
    print("Memory Status")
    print("="*60)
    print(f"Total RAM: ~256 KB (256,000 bytes)")
    print(f"Available to Python: {total:,} bytes ({total/1024:.1f} KB)")
    print(f"Currently allocated: {mem_alloc:,} bytes ({mem_alloc/1024:.1f} KB)")
    print(f"Currently free: {mem_free:,} bytes ({mem_free/1024:.1f} KB)")
    print(f"Free percentage: {mem_free/total*100:.1f}%")


# Auto-run when imported
if __name__ == "__main__":
    check_available_memory()
    measure_all_imports()
else:
    # When imported as module, show help
    print("\nCircuitPython Import Memory Measurement Tool")
    print("="*60)
    print("Functions available:")
    print("  measure_imports.check_available_memory()")
    print("  measure_imports.measure_all_imports()")
    print("  measure_imports.measure_single_module('module_name')")
    print("\nExample:")
    print("  >>> import measure_imports")
    print("  >>> measure_imports.measure_single_module('adafruit_ble')")
