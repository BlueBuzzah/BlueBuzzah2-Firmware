# PlatformIO CLI Reference for nRF52840 Development

Complete command reference for building, flashing, testing, and debugging Adafruit nRF52840 projects.

## Essential Commands

### Build & Flash

```bash
# Compile firmware
pio run

# Compile specific environment
pio run -e adafruit_feather_nrf52840

# Flash to connected device
pio run -t upload

# Flash specific environment
pio run -e adafruit_feather_nrf52840 -t upload

# Clean build artifacts
pio run -t clean

# Full rebuild (clean + build)
pio run -t clean && pio run
```

### Serial Monitor

```bash
# Open serial monitor (default baud from platformio.ini)
pio device monitor

# Specify baud rate
pio device monitor -b 115200

# Monitor with timestamp
pio device monitor --filter time

# Monitor specific port
pio device monitor -p /dev/cu.usbmodem14201

# List available serial ports
pio device list
```

### Testing

```bash
# Run all tests on native platform
pio test -e native

# Run specific test suite
pio test -e native -f test_state_machine

# Run with verbose output
pio test -e native -v

# Run tests with coverage
pio test -e native_coverage
```

## Project Configuration

### platformio.ini Structure

```ini
[env:adafruit_feather_nrf52840]
platform = nordicnrf52
board = adafruit_feather_nrf52840
framework = arduino
monitor_speed = 115200
upload_protocol = nrfutil
board_build.filesystem = littlefs

build_flags =
    -DCFG_DEBUG=0
    -DNRF52840_XXAA
    -w

lib_deps =
    adafruit/Adafruit DRV2605 Library@^1.2.4
    adafruit/Adafruit NeoPixel@^1.12.0
    adafruit/Adafruit BusIO@^1.16.1
    wifwaf/TCA9548A@^1.1.3
```

### Native Test Environment

```ini
[env:native]
platform = native
test_framework = unity
build_flags =
    -DUNITY_INCLUDE_CONFIG_H
    -DNATIVE_TEST_BUILD
    -DPIO_UNIT_TESTING
    -DARDUINO=100
    -std=c++11
    -g
    -I include
    -I test/mocks/src

build_src_filter =
    +<*>
    -<main.cpp>
    -<ble_manager.cpp>
    -<hardware.cpp>

test_build_src = true
lib_compat_mode = off
```

### Coverage Environment (LLVM/macOS)

```ini
[env:native_coverage]
platform = native
test_framework = unity
build_flags =
    -DUNITY_INCLUDE_CONFIG_H
    -DNATIVE_TEST_BUILD
    -O0
    -fprofile-instr-generate
    -fcoverage-mapping
    -I include
    -I test/mocks/src

extra_scripts = scripts/coverage_flags.py
```

### Coverage Environment (GCC/Linux)

```ini
[env:native_coverage_gcc]
platform = native
test_framework = unity
build_flags =
    -DUNITY_INCLUDE_CONFIG_H
    -DNATIVE_TEST_BUILD
    -O0
    --coverage
    -I include
    -I test/mocks/src

extra_scripts = scripts/coverage_flags_gcc.py
```

## Build Flags Reference

### Common Flags

| Flag | Purpose |
|------|---------|
| `-DCFG_DEBUG=0` | Disable Bluefruit debug output |
| `-DCFG_DEBUG=1` | Enable Bluefruit debug output |
| `-DNRF52840_XXAA` | MCU variant identifier |
| `-w` | Suppress warnings |
| `-Wall` | Enable all warnings |
| `-Werror` | Treat warnings as errors |

### Optimization Flags

| Flag | Purpose |
|------|---------|
| `-O0` | No optimization (for debugging) |
| `-O2` | Optimize for speed |
| `-Os` | Optimize for size |
| `-Og` | Optimize for debugging |

### Debug Flags

| Flag | Purpose |
|------|---------|
| `-g` | Include debug symbols |
| `-ggdb` | Include GDB-specific debug info |
| `-DDEBUG` | Define DEBUG macro |

## Library Management

```bash
# Search for libraries
pio lib search "drv2605"

# Install library
pio lib install "Adafruit DRV2605 Library"

# Install specific version
pio lib install "Adafruit DRV2605 Library@1.2.4"

# Update all libraries
pio lib update

# List installed libraries
pio lib list

# Remove library
pio lib uninstall "Adafruit DRV2605 Library"
```

## Coverage Workflow

### LLVM Coverage (macOS)

```bash
# Run tests with coverage instrumentation
pio test -e native_coverage

# Merge profile data
xcrun llvm-profdata merge -sparse default.profraw -o default.profdata

# Generate text report
xcrun llvm-cov report .pio/build/native_coverage/program \
    -instr-profile=default.profdata

# Generate HTML report
xcrun llvm-cov show .pio/build/native_coverage/program \
    -instr-profile=default.profdata \
    -format=html \
    -output-dir=coverage

# View specific file coverage
xcrun llvm-cov show .pio/build/native_coverage/program \
    -instr-profile=default.profdata \
    src/state_machine.cpp
```

### GCC Coverage (Linux CI)

```bash
# Run tests with gcov instrumentation
pio test -e native_coverage_gcc

# Generate coverage report
gcov -o .pio/build/native_coverage_gcc src/*.cpp

# Generate HTML with lcov
lcov --capture --directory . --output-file coverage.info
genhtml coverage.info --output-directory coverage
```

## Filesystem Operations

### LittleFS

```bash
# Build filesystem image
pio run -t buildfs

# Upload filesystem
pio run -t uploadfs

# Erase filesystem
pio run -t erasefs
```

## Advanced Commands

### Verbose Output

```bash
# Verbose build
pio run -v

# Very verbose (show all compiler commands)
pio run -vvv
```

### Multiple Environments

```bash
# Build all environments
pio run

# Build specific environments
pio run -e native -e adafruit_feather_nrf52840

# Test all environments
pio test
```

### CI/CD Commands

```bash
# Check project configuration
pio check

# Static analysis
pio check --skip-packages

# Generate compile_commands.json
pio run -t compiledb

# Export for IDE
pio project init --ide vscode
```

## Troubleshooting

### Common Issues

| Issue | Solution |
|-------|----------|
| Upload fails | Check USB connection, try different cable |
| Port not found | Run `pio device list`, check permissions |
| Library not found | Run `pio lib install` or check lib_deps |
| Build fails after update | Run `pio run -t clean` |
| Wrong board detected | Specify `-e environment` explicitly |

### Reset Device

```bash
# If device is unresponsive, double-tap reset button
# to enter bootloader mode (LED pulses red)

# Then upload
pio run -t upload
```

### Debug Build

```bash
# Build with debug symbols
pio run -e adafruit_feather_nrf52840 --target debug

# If using J-Link
pio debug

# Start GDB session
pio debug --interface=gdb
```

## Extra Scripts

### coverage_flags.py (LLVM)

```python
Import("env")
env.Append(LINKFLAGS=["-fprofile-instr-generate"])
```

### coverage_flags_gcc.py (GCC)

```python
Import("env")
env.Append(LINKFLAGS=["--coverage"])
```

### Custom Upload Script

```python
Import("env")

def before_upload(source, target, env):
    print("Preparing to upload...")

def after_upload(source, target, env):
    print("Upload complete!")

env.AddPreAction("upload", before_upload)
env.AddPostAction("upload", after_upload)
```

## Environment Variables

| Variable | Purpose |
|----------|---------|
| `PLATFORMIO_CORE_DIR` | PlatformIO core directory |
| `PLATFORMIO_HOME_DIR` | PlatformIO home (~/.platformio) |
| `PLATFORMIO_BUILD_FLAGS` | Additional build flags |
| `PLATFORMIO_UPLOAD_PORT` | Override upload port |

## Quick Reference Card

```bash
# Daily workflow
pio run                    # Build
pio run -t upload          # Flash
pio device monitor         # Monitor serial

# Testing
pio test -e native         # Run tests
pio test -e native -v      # Verbose tests
pio test -e native_coverage # With coverage

# Maintenance
pio run -t clean           # Clean build
pio lib update             # Update libraries
pio upgrade                # Upgrade PlatformIO
```
