# BlueBuzzah Project - CircuitPython Development Guide

## Quick Reference

| Specification     | Value                                  | Impact                            |
| ----------------- | -------------------------------------- | --------------------------------- |
| **Board**         | Adafruit Feather nRF52840 Express      | Nordic SoC with BLE 5.0           |
| **MCU**           | nRF52840                               | ARM Cortex-M4F @ 64MHz            |
| **RAM**           | 256 KB total                           | ~130KB available to CircuitPython |
| **Flash**         | 1 MB                                   | ~850KB for user code/libs         |
| **CircuitPython** | v9.2.x                                 | Subset of Python 3.4              |
| **BLE Active**    | -40KB RAM                              | ~90KB RAM remaining               |
| **Key Features**  | BLE 5.0, USB, I2C, SPI, UART, NeoPixel | Hardware peripherals              |

---

**⚠️ CRITICAL INSTRUCTION FOR CLAUDE CODE ⚠️**

**ALWAYS use the `circuitpython-expert` agent for ANY CircuitPython task in this project.**

Invoke via Task tool: `subagent_type: "circuitpython-expert"`

The agent has memory profiling, nRF52840 expertise, and CircuitPython v9.2.x API knowledge.

---

## Project Context

This project uses **CircuitPython v9.2.x** running on an **Adafruit Feather nRF52840 Express** board with BLE functionality for vibrotactile haptic feedback applications.

## 🚨 MANDATORY: Use CircuitPython Expert Agent 🚨

**CRITICAL REQUIREMENT**: For ALL CircuitPython-related tasks in this project, you MUST use the `circuitpython-expert` agent.

### When to Use the Agent

Use the agent for **ANY** task involving:

- ✅ Writing new CircuitPython code
- ✅ Reviewing existing CircuitPython code
- ✅ Debugging memory issues or errors
- ✅ Optimizing code for memory/performance
- ✅ Implementing BLE functionality
- ✅ Working with hardware peripherals (I2C, SPI, GPIO, ADC)
- ✅ Analyzing import costs or module usage
- ✅ Refactoring CircuitPython code
- ✅ Answering questions about CircuitPython implementation

### How to Invoke the Agent

**Use the Task tool with `circuitpython-expert` subagent:**

```
Task tool with:
  subagent_type: "circuitpython-expert"
  prompt: "[detailed description of the task]"
  description: "[5-10 word summary]"
```

**Example invocations:**

```
Task:
  subagent_type: "circuitpython-expert"
  prompt: "Review src/main.py for memory optimization opportunities. Check for string operations in loops, missing const() usage, and unused imports. Apply profiling skill and suggest specific optimizations."
  description: "Review and optimize main.py memory usage"
```

```
Task:
  subagent_type: "circuitpython-expert"
  prompt: "Implement BLE GATT service for haptic feedback control with characteristics for intensity (uint8) and pattern (uint8 array). Pre-allocate all buffers, use const() for UUIDs, ensure memory stays above 10KB free."
  description: "Implement BLE haptic control service"
```

### Agent Capabilities

The `circuitpython-expert` agent has:

- Deep knowledge of nRF52840 hardware constraints
- CircuitPython v9.2.x API expertise
- Memory optimization strategies
- Access to the `profiling-circuitpython-memory` skill
- BLE implementation patterns
- Hardware peripheral interface knowledge

### Agent Workflow Integration

The agent automatically:

1. **Analyzes memory implications** before writing code
2. **Uses the profiling skill** to detect memory waste patterns
3. **Applies optimization templates** for common issues
4. **Validates code** against CircuitPython v9.2.x constraints
5. **Provides byte-count estimates** for memory impact
6. **Tests compatibility** with nRF52840 limitations

### NEVER Skip the Agent

**DON'T** write CircuitPython code directly - ALWAYS use the agent first.

The agent will ensure:

- No type hints (causes SyntaxError)
- Proper const() usage for numeric constants
- Pre-allocated buffers instead of loop allocations
- Correct import strategies
- Memory-efficient patterns
- Hardware-appropriate implementations

## Critical CircuitPython Documentation

### Official Documentation References

**ALWAYS refer to these official CircuitPython v9.2.x documentation sources:**

1. **Shared Bindings (Core APIs)**:

   - https://docs.circuitpython.org/en/9.2.x/shared-bindings/index.html
   - Contains all CircuitPython-specific modules (board, busio, digitalio, analogio, etc.)

2. **Supported Python Built-ins**:

   - https://docs.circuitpython.org/en/9.2.x/docs/library/index.html
   - Shows which standard Python libraries and built-ins are available

3. **CircuitPython Design Guide**:
   - https://docs.circuitpython.org/projects/bundle/en/latest/docs/design_guide.html
   - Best practices for memory-constrained environments

## Memory Management Rules

### Critical Memory Constraints

- **Available RAM**: ~130KB without BLE, ~90KB with BLE active
- **Heap fragmentation**: Major issue - allocate large buffers once at startup
- **String operations**: Very expensive - each concatenation allocates new memory
- **Collection overhead**: Lists/dicts have significant memory overhead

### Required Memory Patterns

**ALWAYS use const() for numeric constants** - Saves RAM by storing in flash:

- Syntax: `from micropython import const` then `MY_CONST = const(42)`
- Zero RAM usage vs regular assignment which uses RAM

**Pre-allocate all buffers at startup** - Never allocate in loops:

- Create bytearrays once and reuse via slicing or memoryview
- Use `read_into()` methods instead of `read()` to avoid allocations

**Monitor memory during development**:

- Call `gc.collect()` then `gc.mem_free()` to check available memory
- Memory drops below 10KB risk allocation failures

## Import Strategy

### Import Order and Optimization

**Import large modules first** to avoid fragmentation:

- Start with `_bleio` (if using BLE) as it's the largest
- Follow with `board`, `busio`, other hardware modules
- Call `gc.collect()` after large imports
- Import specific items from modules: `from digitalio import DigitalInOut, Direction`

**Never import entire modules** when you need specific items - wastes RAM

## Language Constraints

### CircuitPython Does NOT Support

1. **Type hints** - Syntax error if used (no `: str`, `-> int`, etc.)
2. **Dataclasses** - Module doesn't exist
3. **Match/case** - Python 3.10+ feature not available
4. **Walrus operator** `:=` - Python 3.8+ feature
5. **F-string `=` specifier** - `f"{var=}"` causes SyntaxError
6. **Asyncio** - No async/await support
7. **Threading/multiprocessing** - Single-threaded only
8. **\_\_slots\_\_** - Not implemented
9. **Multiple inheritance** - Keep inheritance simple
10. **Deep recursion** - Stack limited to ~20-30 calls

### String Handling Rules

- **Avoid concatenation** - Each `+` creates new string object
- **Use .format()** for single-use strings
- **Use bytearray** for strings that change frequently
- **struct.pack_into()** for binary data - most memory efficient

## BLE-Specific Requirements

### Memory Impact

BLE activation consumes **20-40KB RAM immediately**:

- Base BLE stack: ~20KB
- Each connection: ~2-3KB additional
- Each characteristic with notify: ~512 bytes buffer
- Advertisement data: ~1KB

### BLE Development Rules

- **Pre-allocate advertisement data** - Never recreate during advertising
- **Reuse characteristic buffers** - Don't allocate per write/notify
- **Monitor connection count** - Each uses precious RAM
- **Set appropriate MTU** - nRF52840 max is 247 bytes
- **Call gc.collect()** after BLE operations to reclaim memory

## Hardware Patterns (nRF52840)

### Pin Management

**Pins are singletons** - Creating `DigitalInOut(board.D5)` twice returns same object:

- Initialize pins once at startup
- Store references in a class or global
- Never recreate pin objects in loops or functions

### Power Management

**Deep sleep** (`alarm.exit_and_deep_sleep_until_alarms()`):

- Lowest power, loses RAM contents
- Wake via time or pin alarms
- Restarts from beginning of code.py

**Light sleep** (`alarm.light_sleep_until_alarms()`):

- Maintains RAM, faster wake
- Higher power consumption than deep sleep
- Continues execution after sleep

**Cooperative multitasking** - Use `time.sleep(0)` to yield to system tasks (USB, BLE)

## File System Rules

### CIRCUITPY Drive Constraints

- **Total space**: ~850KB available for user files after CircuitPython
- **Write limitation**: Cannot write while USB connected (unless configured in boot.py)
- **Flash wear**: Limited write cycles (10,000-100,000 per block)
- **Boot sequence**: boot.py executes first (configure USB/storage), then code.py/main.py

### Storage Configuration

**boot.py controls USB write access** - Must choose at boot:

- Either USB can write (normal mode for development)
- Or CircuitPython can write (for data logging)
- Cannot have both simultaneously
- Use pin state at boot to decide mode

## Module Reference

### Memory Impact by Module

| Module      | RAM Usage    | When to Import        |
| ----------- | ------------ | --------------------- |
| `_bleio`    | 20-40KB      | Only if using BLE     |
| `busio`     | ~2KB per bus | Only for I2C/SPI/UART |
| `displayio` | 10-20KB      | Only for displays     |
| `board`     | Minimal      | Always safe           |
| `digitalio` | <1KB         | Always safe           |
| `analogio`  | <1KB         | Always safe           |
| `time`      | Minimal      | Always safe           |
| `gc`        | Built-in     | Always available      |
| `struct`    | Minimal      | For binary data       |
| `json`      | ~2-5KB       | Avoid if possible     |

## Error Reference

| Error                        | Cause                       | Fix                                                                |
| ---------------------------- | --------------------------- | ------------------------------------------------------------------ |
| `MemoryError`                | Out of RAM                  | **USE AGENT**: Run memory profiler, apply optimizations            |
| `OSError: 28`                | Flash storage full          | Delete files, use smaller libraries                                |
| `OSError: 30`                | USB has write access        | Configure boot.py for CircuitPython write                          |
| `RuntimeError: Corrupt heap` | Memory corruption           | **USE AGENT**: Review code for buffer overruns, check array bounds |
| `ImportError`                | Module not in CircuitPython | **USE AGENT**: Verify module availability in v9.2.x                |
| `SyntaxError` at type hint   | Type hints not supported    | **USE AGENT**: Remove all type annotations                         |

**For ANY error**: Invoke the `circuitpython-expert` agent for expert analysis and resolution.

## Performance Guidelines

### Timing and Loops

- **Use `time.monotonic()`** for timing - won't go backwards
- **`time.monotonic_ns()`** for microsecond precision (returns nanoseconds)
- **Always include `time.sleep(0)`** in tight loops - yields to system
- **Avoid `time.sleep()` under 0.001** - precision limited

### Optimization Priorities

1. **Memory over speed** - RAM is the limiting factor
2. **Simplicity over features** - Complex code uses more memory
3. **Reuse over recreation** - Object creation is expensive
4. **Binary over text** - struct.pack is efficient for data

## Development Checklist

### Before Writing Code

✓ **INVOKE circuitpython-expert agent** - MANDATORY for all CircuitPython tasks
✓ Check module exists in CircuitPython 9.2.x docs
✓ Verify API matches CircuitPython (not standard Python)
✓ Consider BLE memory impact if using Bluetooth
✓ Plan buffer allocation strategy
✓ Remove ALL type hints

### During Development

✓ **Use circuitpython-expert agent** for implementation
✓ Use const() for all numeric constants
✓ Pre-allocate buffers outside loops
✓ Import only needed items from modules
✓ Monitor memory with gc.mem_free()
✓ Test on actual hardware (not emulator)

### After Implementation

✓ **Run memory profiler** via circuitpython-expert agent
✓ Address HIGH severity issues (unused imports, loop allocations)
✓ Apply const() conversions (MEDIUM severity)
✓ Verify optimizations on actual device
✓ Ensure free memory stays above 10KB

### Common Mistakes to Avoid

✗ DON'T write CircuitPython code without using the agent
✗ DON'T use type hints - causes SyntaxError
✗ DON'T allocate in loops - causes MemoryError
✗ DON'T use desktop Python patterns - won't work
✗ DON'T create large dicts/sets - too much RAM
✗ DON'T forget gc.collect() - memory won't free
✗ DON'T recreate pin objects - wastes memory
✗ DON'T use recursion - limited stack depth
✗ DON'T skip memory profiling after changes

---

_Document Version: 3.0 - CircuitPython 9.2.x development guide with mandatory agent usage and memory profiling integration for nRF52840_
- Do not document or comment, or even write code, that emphasizes 'migration' because this project is currently net-new.