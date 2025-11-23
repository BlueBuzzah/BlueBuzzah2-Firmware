"""
Basic example of using the CircuitPython memory profiler.
Run this to analyze a CircuitPython source file.
"""

import sys
from pathlib import Path

# Add parent directory to path to import profiler
sys.path.insert(0, str(Path(__file__).parent.parent))

from memory_profiler import MemoryProfiler


def main():
    """Analyze a sample CircuitPython file."""

    # Sample code to analyze (typical blinky with issues)
    sample_code = '''
import board
import digitalio
import time
import displayio  # Not used!

# Constants without const()
LED_PIN = board.D13
BLINK_DELAY = 0.5

# String concatenation in loop (bad!)
message = ""
for i in range(10):
    message = message + str(i) + ","

# Growing list (fragments heap)
readings = []
for i in range(100):
    readings.append(i * 2)

# LED blink
led = digitalio.DigitalInOut(LED_PIN)
led.direction = digitalio.Direction.OUTPUT

while True:
    led.value = not led.value
    time.sleep(BLINK_DELAY)
'''

    # Write sample to temp file
    sample_file = Path("/tmp/sample_circuitpy.py")
    sample_file.write_text(sample_code)

    # Run profiler
    print("Analyzing sample CircuitPython code...\n")
    profiler = MemoryProfiler(str(sample_file))
    report = profiler.analyze()

    # Display results
    print("=" * 70)
    print("Memory Profile Results")
    print("=" * 70)

    summary = report['summary']
    print(f"\nEstimated peak memory: {summary['estimated_peak_memory']:,} bytes")
    print(f"Available after allocations: {summary['available_memory']:,} bytes")
    print(f"Memory margin: {summary['available_memory'] / 131072 * 100:.1f}%")
    print(f"GC pressure: {summary['gc_pressure']}")
    print(f"Fragmentation risk: {summary['fragmentation_risk']}")

    print("\n" + "=" * 70)
    print(f"Issues Found: {len(report['critical_issues'])}")
    print("=" * 70)

    for i, issue in enumerate(report['critical_issues'], 1):
        print(f"\n{i}. [{issue['severity']}] Line {issue['line']}: {issue['issue']}")
        print(f"   Code: {issue['code']}")
        print(f"   Impact: {issue['memory_waste']}")
        print(f"   Fix: {issue['fix'][:70]}")

    # Import analysis
    print("\n" + "=" * 70)
    print("Import Analysis")
    print("=" * 70)
    imports = report['import_analysis']
    print(f"Total import cost: {imports['total_cost']:,} bytes")

    if imports['unused_imports']:
        print(f"\nUnused imports detected: {', '.join(imports['unused_imports'])}")
        print("Recommendation: Remove these to free memory")

    print("\n" + "=" * 70)
    print("Optimization Priority")
    print("=" * 70)
    print("1. Remove unused 'displayio' import → Save 8KB")
    print("2. Fix string concatenation loop → Save ~500 bytes")
    print("3. Pre-allocate readings list → Reduce fragmentation")
    print("4. Use const() for LED_PIN, BLINK_DELAY → Save 8-16 bytes")


if __name__ == "__main__":
    main()
