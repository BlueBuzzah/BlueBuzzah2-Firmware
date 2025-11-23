# CircuitPython Memory Profiling Examples

Examples demonstrating memory profiling and optimization for CircuitPython on nRF52840.

## Files

### profile_basic.py
Basic usage example of the memory profiler.

**Run on development machine:**
```bash
python profile_basic.py
```

Analyzes a sample CircuitPython file and displays:
- Memory usage summary
- Critical issues found
- Import analysis
- Optimization recommendations

### before_after.py
Side-by-side comparison of inefficient vs optimized code patterns.

**Run on development machine:**
```bash
python before_after.py
```

Shows five common memory issues:
1. String concatenation in loops
2. List growth via append()
3. Constants using RAM instead of flash
4. File read() allocations
5. String vs bytes operations

### measure_imports.py
Tool to measure actual import costs on the nRF52840 board.

**Run on nRF52840:**
1. Copy `measure_imports.py` to CIRCUITPY drive
2. Connect via serial: `screen /dev/ttyACM0 115200` (or COM port on Windows)
3. Press Ctrl+C to enter REPL
4. Import and run:
```python
>>> import measure_imports
>>> measure_imports.measure_all_imports()
```

Or measure a single module:
```python
>>> import measure_imports
>>> measure_imports.measure_single_module("adafruit_ble")
```

Results can be added to `import_costs.py` database.

## Usage Workflow

### 1. Develop Feature
Write your CircuitPython code normally.

### 2. Profile Code
```bash
cd ..  # Go to skill root directory
python memory_profiler.py your_code.py --suggest
```

### 3. Review Issues
Check output for critical memory problems:
- Unused imports (HIGH priority)
- String operations in loops (HIGH priority)
- Missing const() usage (LOW priority)

### 4. Study Examples
```bash
python examples/before_after.py
```

Find the pattern matching your issue and apply the optimized version.

### 5. Test on Device
Copy optimized code to CIRCUITPY and verify:
```python
import gc
gc.collect()
print(f"Free memory: {gc.mem_free()} bytes")
```

Ensure free memory stays above 10KB during operation.

### 6. Measure Actual Impact (Optional)
Use `measure_imports.py` to verify import costs or measure runtime memory usage.

## Common Patterns Reference

### String Building
**Bad:**
```python
msg = ""
for x in data:
    msg = msg + str(x)
```

**Good:**
```python
from micropython import const
BUFFER_SIZE = const(100)
buffer = bytearray(BUFFER_SIZE)
# Use buffer slicing
```

### List Growth
**Bad:**
```python
readings = []
for i in range(100):
    readings.append(sensor.read())
```

**Good:**
```python
from micropython import const
MAX = const(100)
readings = [None] * MAX
for i in range(MAX):
    readings[i] = sensor.read()
```

### Constants
**Bad:**
```python
TIMEOUT = 1000
ADDR = 0x48
```

**Good:**
```python
from micropython import const
TIMEOUT = const(1000)
ADDR = const(0x48)
```

### File Operations
**Bad:**
```python
data = file.read()
```

**Good:**
```python
from micropython import const
SIZE = const(256)
buffer = bytearray(SIZE)
n = file.readinto(buffer)
data = buffer[:n]
```

## Tips

- Profile early and often during development
- Focus on HIGH severity issues first
- Test on actual hardware (emulators don't show memory issues)
- Keep minimum 10KB free RAM during operation
- Call `gc.collect()` after large operations
- Monitor memory with `gc.mem_free()` at critical points

## Troubleshooting

**Profiler reports no issues but getting MemoryError:**
- Run runtime profiling (not yet implemented in profiler)
- Manually instrument code with gc.mem_free() calls
- Check for memory issues in imported libraries

**Import costs seem different:**
- CircuitPython versions differ in module sizes
- Some modules have platform-specific implementations
- Re-measure using measure_imports.py on your setup

**Optimization doesn't help:**
- Verify the issue is memory, not CPU/timing
- Check if BLE is active (uses 20-40KB)
- Review imported libraries (displayio uses 8KB+)
