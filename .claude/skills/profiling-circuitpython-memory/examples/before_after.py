"""
Before/after optimization examples for CircuitPython memory usage.
Shows common memory issues and their optimized versions.
"""


def example_1_string_concatenation():
    """String concatenation in loops - major memory waste."""
    print("\n" + "="*70)
    print("Example 1: String Concatenation")
    print("="*70)

    print("\n### BEFORE (Inefficient) ###")
    print('''
def build_message_bad(sensor_readings):
    """Allocates new string on every iteration."""
    message = "Readings: "
    for reading in sensor_readings:
        message = message + str(reading) + ", "  # BAD: Creates new string!
    return message

# Memory impact: ~100-500 bytes per iteration
# With 20 readings: ~2-10 KB wasted
''')

    print("\n### AFTER (Optimized) ###")
    print('''
from micropython import const

def build_message_good(sensor_readings):
    """Reuses pre-allocated buffer."""
    BUFFER_SIZE = const(256)
    buffer = bytearray(BUFFER_SIZE)
    prefix = b"Readings: "
    buffer[0:len(prefix)] = prefix
    offset = len(prefix)

    for reading in sensor_readings:
        reading_bytes = str(reading).encode()
        buffer[offset:offset+len(reading_bytes)] = reading_bytes
        offset += len(reading_bytes)
        buffer[offset:offset+2] = b", "
        offset += 2

    return bytes(buffer[:offset]).decode()

# Memory impact: Fixed 256 bytes, reusable
# Savings: 2-10 KB depending on loop iterations
''')


def example_2_list_preallocation():
    """List growth via append() causes heap fragmentation."""
    print("\n" + "="*70)
    print("Example 2: List Pre-allocation")
    print("="*70)

    print("\n### BEFORE (Inefficient) ###")
    print('''
def collect_readings_bad(sensor, count):
    """List grows dynamically, fragments heap."""
    readings = []
    for i in range(count):
        readings.append(sensor.read())  # BAD: Reallocates list!
    return readings

# Memory impact: Multiple reallocations, fragmentation
# List may be copied 5-10 times during growth
''')

    print("\n### AFTER (Optimized) ###")
    print('''
from micropython import const

def collect_readings_good(sensor, count):
    """Pre-allocates list to exact size."""
    MAX_READINGS = const(100)
    readings = [None] * min(count, MAX_READINGS)

    for i in range(len(readings)):
        readings[i] = sensor.read()

    return readings

# Memory impact: Single allocation, no fragmentation
# Savings: 20-40% faster, no wasted copies
''')


def example_3_const_usage():
    """Constants should be stored in flash, not RAM."""
    print("\n" + "="*70)
    print("Example 3: const() for Constants")
    print("="*70)

    print("\n### BEFORE (Inefficient) ###")
    print('''
# All these values use RAM
I2C_ADDRESS = 0x48
BUFFER_SIZE = 64
TIMEOUT_MS = 1000
SAMPLE_RATE = 100

# Memory impact: 4-8 bytes per constant = 16-32 bytes RAM
''')

    print("\n### AFTER (Optimized) ###")
    print('''
from micropython import const

# Values stored in flash (ROM), zero RAM usage
I2C_ADDRESS = const(0x48)
BUFFER_SIZE = const(64)
TIMEOUT_MS = const(1000)
SAMPLE_RATE = const(100)

# Memory impact: 0 bytes RAM, stored in flash
# Savings: 16-32 bytes per group of constants
''')


def example_4_file_operations():
    """File read() allocates buffer dynamically."""
    print("\n" + "="*70)
    print("Example 4: File Read Operations")
    print("="*70)

    print("\n### BEFORE (Inefficient) ###")
    print('''
def load_config_bad(filename):
    """Allocates new buffer for file contents."""
    with open(filename, "rb") as f:
        data = f.read()  # BAD: Allocates buffer!
    return data

# Memory impact: Allocates buffer size of file
# Not reusable, must be garbage collected
''')

    print("\n### AFTER (Optimized) ###")
    print('''
from micropython import const

# Pre-allocate buffer once, reuse for all reads
CONFIG_BUFFER_SIZE = const(512)
config_buffer = bytearray(CONFIG_BUFFER_SIZE)

def load_config_good(filename):
    """Reuses pre-allocated buffer."""
    with open(filename, "rb") as f:
        bytes_read = f.readinto(config_buffer)
    return config_buffer[:bytes_read]

# Memory impact: Fixed 512 bytes, reusable
# Savings: No per-call allocation
''')


def example_5_bytes_vs_strings():
    """Bytes operations are more memory-efficient than strings."""
    print("\n" + "="*70)
    print("Example 5: Bytes vs Strings")
    print("="*70)

    print("\n### BEFORE (Inefficient) ###")
    print('''
def send_command_bad(uart, cmd, value):
    """String building allocates multiple objects."""
    message = "AT+" + cmd + "=" + str(value) + "\\r\\n"
    uart.write(message.encode())  # Convert to bytes at end

# Memory impact: 4 string allocations + final bytes
# Each concatenation creates new string object
''')

    print("\n### AFTER (Optimized) ###")
    print('''
from micropython import const

COMMAND_BUFFER_SIZE = const(32)
cmd_buffer = bytearray(COMMAND_BUFFER_SIZE)

def send_command_good(uart, cmd, value):
    """Direct bytes assembly in buffer."""
    prefix = b"AT+"
    suffix = b"\\r\\n"

    # Assemble directly in buffer
    offset = 0
    cmd_buffer[offset:offset+len(prefix)] = prefix
    offset += len(prefix)

    cmd_bytes = cmd.encode()
    cmd_buffer[offset:offset+len(cmd_bytes)] = cmd_bytes
    offset += len(cmd_bytes)

    cmd_buffer[offset] = ord('=')
    offset += 1

    value_bytes = str(value).encode()
    cmd_buffer[offset:offset+len(value_bytes)] = value_bytes
    offset += len(value_bytes)

    cmd_buffer[offset:offset+len(suffix)] = suffix
    offset += len(suffix)

    uart.write(cmd_buffer[:offset])

# Memory impact: Fixed 32-byte buffer, reusable
# Savings: No string allocations, direct bytes ops
''')


def main():
    """Display all before/after examples."""
    print("\n" + "="*70)
    print("CircuitPython Memory Optimization Examples")
    print("nRF52840: 256KB RAM total, ~130KB available")
    print("="*70)

    example_1_string_concatenation()
    example_2_list_preallocation()
    example_3_const_usage()
    example_4_file_operations()
    example_5_bytes_vs_strings()

    print("\n" + "="*70)
    print("Key Takeaways")
    print("="*70)
    print("""
1. Pre-allocate buffers outside loops, reuse them
2. Use const() for all numeric constants
3. Prefer bytes operations over string concatenation
4. Pre-allocate lists to exact size instead of append()
5. Use readinto() instead of read() for file operations
6. Minimize string formatting in loops
7. Call gc.collect() after large operations

Total potential savings: 5-20 KB depending on code patterns
""")


if __name__ == "__main__":
    main()
