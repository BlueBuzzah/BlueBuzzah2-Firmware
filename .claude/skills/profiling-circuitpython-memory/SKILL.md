---
name: profiling-circuitpython-memory
description: Analyzes CircuitPython code for memory waste on nRF52840 (256KB SRAM), identifies string operations, large allocations, and import costs. Use when optimizing memory usage, debugging MemoryError, or reducing RAM consumption.
---

# CircuitPython Memory Profiling

Analyzes source code for memory waste patterns and provides actionable optimizations for the Adafruit Feather nRF52840 Express running CircuitPython 9.2.x.

## Quick Start

**Analyze a file**:

```bash
python memory_profiler.py code.py
```

**Get optimization suggestions**:

```bash
python memory_profiler.py code.py --suggest
```

**Measure actual runtime memory**:

```bash
python memory_profiler.py code.py --runtime
```

## Memory Constraints (nRF52840)

- Total RAM: 256 KB
- Available after boot: ~130 KB
- With BLE active: ~90 KB
- Minimum free to avoid errors: 10 KB

## Analysis Workflow

**Step 1: Static Analysis**

Run profiler to identify problematic patterns:

```bash
python memory_profiler.py src/main.py
```

Reviews code for:
- Import costs (measured database in [import_costs.py](import_costs.py))
- String concatenation in loops
- Dynamic list growth
- Large allocations
- Missing const() usage

**Step 2: Review Critical Issues**

Profiler outputs prioritized list sorted by memory impact:

```
CRITICAL ISSUES (3 found):
  Line 45: String concatenation in loop
    Impact: ~500 bytes/iteration
    Fix: Use pre-allocated bytearray(100)

  Line 12: Unused import 'displayio'
    Impact: 8192 bytes
    Fix: Remove import
```

**Step 3: Apply Optimizations**

Use suggested fixes from profiler output. See [optimizer.py](optimizer.py) for automated transformations.

**Step 4: Verify**

Measure actual memory usage on device:

```bash
python memory_profiler.py --runtime src/main.py
# Copies instrumented code to board, measures gc.mem_free()
```

## Pattern Detection

Profiler identifies these high-impact patterns (full list in [patterns.py](patterns.py)):

**String Operations**:
- Concatenation: `msg = msg + str(x)` → Use bytearray
- Formatting in loops: `f"{value}"` → Pre-format once
- Repeated literals: Store in const() bytes

**Allocations**:
- Growing lists: `data.append(x)` → Pre-allocate with size
- Dictionary creation: Minimize, use tuples where possible
- Buffer recreation: Allocate once, reuse via slicing

**Imports**:
- Unused modules: Remove entirely
- Large modules: Check if needed (displayio: 8KB, adafruit_ble: 20KB)
- Selective imports: `from busio import I2C` (note: doesn't save memory, but improves clarity)

## Optimization Templates

**String Building**:

```python
# Before (allocates new string each iteration)
result = ""
for value in data:
    result = result + str(value) + ","

# After (reuses buffer)
from micropython import const
BUFFER_SIZE = const(100)
buffer = bytearray(BUFFER_SIZE)
offset = 0
for value in data:
    temp = str(value).encode()
    buffer[offset:offset+len(temp)] = temp
    offset += len(temp)
    buffer[offset] = ord(',')
    offset += 1
```

**List Pre-allocation**:

```python
# Before (grows dynamically, fragments heap)
readings = []
for i in range(100):
    readings.append(sensor.read())

# After (allocates once)
from micropython import const
MAX_READINGS = const(100)
readings = [None] * MAX_READINGS
for i in range(MAX_READINGS):
    readings[i] = sensor.read()
```

**Constant Folding**:

```python
# Before (stores in RAM)
SENSOR_ADDR = 0x48
BUFFER_SIZE = 64

# After (stores in flash)
from micropython import const
SENSOR_ADDR = const(0x48)
BUFFER_SIZE = const(64)
```

## Output Format

**Summary Section**:

```
Memory Profile Summary
----------------------
Estimated peak: 18,432 bytes
Available: 131,072 bytes
Margin: 112,640 bytes (86%)
GC pressure: HIGH (10+ allocations in loops)
Fragmentation risk: MEDIUM
```

**Import Analysis**:

```
Import Costs
------------
board: 0 bytes (built-in)
digitalio: 456 bytes
busio: 1,824 bytes
displayio: 8,192 bytes [UNUSED - remove to save 8KB]

Total import cost: 10,472 bytes
```

**Optimization Recommendations**:

```
Recommended Optimizations (by impact)
-------------------------------------
1. Remove unused 'displayio' import → Save 8,192 bytes
2. Pre-allocate line 34 buffer → Save ~2,000 bytes
3. Use const() for line 12-18 → Save 48 bytes
4. Replace string concat line 67 → Save ~500 bytes/iteration
```

## Advanced Features

**Memory Timeline**:

```bash
python memory_profiler.py --runtime --plot code.py
```

Generates memory usage over time graph (requires matplotlib on development machine, not on device).

**Custom Pattern Detection**:

Add patterns to [patterns.py](patterns.py):

```python
{
    "pattern": r"your_regex_here",
    "issue": "Description of problem",
    "fix": "How to fix it",
    "severity": "HIGH|MEDIUM|LOW",
    "memory_impact": "Estimated bytes"
}
```

**Batch Analysis**:

```bash
python memory_profiler.py src/*.py --summary
```

## Integration with Development Workflow

1. Write feature code
2. Run profiler: `python memory_profiler.py code.py`
3. Apply critical fixes (HIGH severity items)
4. Test on device with instrumented runtime profiling
5. Verify gc.mem_free() stays above 10KB threshold
6. Commit optimized code

## False Positives

**Profiler may flag these as issues (ignore them)**:

- One-time string operations outside loops
- Small dictionaries (<10 items) for configuration
- Module imports that are actually needed
- List comprehensions for small, fixed-size data

Use `--runtime` mode to verify actual impact before optimizing.

## Measuring Custom Imports

To add new library costs to database:

```bash
python examples/measure_imports.py adafruit_motor
```

Updates [import_costs.py](import_costs.py) with measured values.

## Files

- **memory_profiler.py**: Main analysis engine
- **patterns.py**: Memory waste pattern database
- **import_costs.py**: Measured import costs for common libraries
- **optimizer.py**: Automated code transformation suggestions
- **examples/profile_basic.py**: Simple usage example
- **examples/before_after.py**: Optimization comparisons
- **examples/measure_imports.py**: Tool to measure library costs

## Limitations

- Static analysis estimates only (use --runtime for actual measurements)
- Cannot detect logic-dependent memory usage
- Does not profile C module internals (e.g., _bleio)
- Assumes typical nRF52840 memory availability
- Pattern matching may miss complex code structures

## Troubleshooting

**MemoryError during profiling**: Profiler itself may use memory. Reduce analysis scope or use --minimal flag.

**Import costs seem wrong**: Re-measure on your specific CircuitPython version using examples/measure_imports.py.

**Runtime profiling fails**: Ensure board is connected and CIRCUITPY drive is mounted. Check boot.py allows CircuitPython write access.
