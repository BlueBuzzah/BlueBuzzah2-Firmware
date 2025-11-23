"""
Code transformation suggestions for CircuitPython memory optimization.
Provides before/after patterns for common memory issues.
"""

import re
from typing import List, Tuple, Optional


class MemoryOptimizer:
    """Suggests code transformations to reduce memory usage."""

    @staticmethod
    def optimize_string_concatenation(code: str, line_num: int) -> Optional[Tuple[str, str]]:
        """
        Convert string concatenation to bytearray pattern.
        Returns (original, optimized) or None if not applicable.
        """
        line = code.split('\n')[line_num - 1]

        # Match: var = var + str or var = var + "string"
        if re.search(r'(\w+)\s*=\s*\1\s*\+', line):
            var_name = re.search(r'(\w+)\s*=', line).group(1)

            before = f"# Before: String concatenation\n{line}"
            after = f"""# After: Pre-allocated buffer
from micropython import const
BUFFER_SIZE = const(100)  # Adjust based on max size
{var_name}_buf = bytearray(BUFFER_SIZE)
{var_name}_len = 0

# In loop, instead of concatenation:
# temp = str(value).encode()
# {var_name}_buf[{var_name}_len:{var_name}_len+len(temp)] = temp
# {var_name}_len += len(temp)
"""
            return (before, after)
        return None

    @staticmethod
    def optimize_list_growth(code: str, line_num: int) -> Optional[Tuple[str, str]]:
        """Convert dynamic list growth to pre-allocation."""
        line = code.split('\n')[line_num - 1]

        if '.append(' in line:
            list_var = re.search(r'(\w+)\.append', line)
            if list_var:
                var_name = list_var.group(1)

                before = f"""# Before: Dynamic list growth
{var_name} = []
for item in data:
    {var_name}.append(process(item))
"""

                after = f"""# After: Pre-allocated list
from micropython import const
MAX_ITEMS = const(100)  # Set to maximum expected size
{var_name} = [None] * MAX_ITEMS
for i, item in enumerate(data):
    if i >= MAX_ITEMS:
        break
    {var_name}[i] = process(item)
# If needed, slice to actual size: {var_name} = {var_name}[:actual_count]
"""
                return (before, after)
        return None

    @staticmethod
    def suggest_const_conversion(code: str, line_num: int) -> Optional[Tuple[str, str]]:
        """Suggest converting numeric constant to const()."""
        line = code.split('\n')[line_num - 1]

        match = re.search(r'([A-Z_]+)\s*=\s*(\d+|0x[0-9a-fA-F]+)', line)
        if match:
            var_name = match.group(1)
            value = match.group(2)

            before = f"# Before: Constant in RAM\n{var_name} = {value}"
            after = f"""# After: Constant in flash (saves RAM)
from micropython import const
{var_name} = const({value})
"""
            return (before, after)
        return None

    @staticmethod
    def optimize_file_read(code: str, line_num: int) -> Optional[Tuple[str, str]]:
        """Convert file.read() to read_into() pattern."""
        line = code.split('\n')[line_num - 1]

        if '.read()' in line:
            before = """# Before: Allocates buffer
data = file.read()
"""
            after = """# After: Pre-allocated buffer
from micropython import const
BUFFER_SIZE = const(256)  # Adjust to max file size
buffer = bytearray(BUFFER_SIZE)
bytes_read = file.readinto(buffer)
# Use buffer[:bytes_read] for actual data
"""
            return (before, after)
        return None

    @staticmethod
    def optimize_format_string(code: str, line_num: int) -> Optional[Tuple[str, str]]:
        """Suggest alternatives to f-strings in loops."""
        line = code.split('\n')[line_num - 1]

        if 'f"' in line or 'f\'' in line:
            before = f"""# Before: F-string formatting
for value in sensor_data:
    msg = f"Reading: {{value}}"
    print(msg)
"""
            after = """# After: Minimal formatting
# Option 1: Direct print (best)
for value in sensor_data:
    print("Reading:", value)

# Option 2: Bytes format (if building message)
from micropython import const
prefix = b"Reading: "
buffer = bytearray(50)
buffer[0:len(prefix)] = prefix
for value in sensor_data:
    val_str = str(value).encode()
    buffer[len(prefix):len(prefix)+len(val_str)] = val_str
    # Use buffer
"""
            return (before, after)
        return None


# Pre-built optimization templates
OPTIMIZATION_TEMPLATES = {
    "string_concat": {
        "before": """# Inefficient: String concatenation in loop
result = ""
for item in data:
    result = result + str(item) + ","
""",
        "after": """# Efficient: Pre-allocated bytearray
from micropython import const
BUFFER_SIZE = const(256)
buffer = bytearray(BUFFER_SIZE)
offset = 0

for item in data:
    item_str = str(item).encode()
    buffer[offset:offset+len(item_str)] = item_str
    offset += len(item_str)
    buffer[offset] = ord(',')
    offset += 1

result = bytes(buffer[:offset]).decode()
""",
        "savings": "~50-500 bytes depending on loop iterations"
    },

    "list_prealloc": {
        "before": """# Inefficient: Growing list
readings = []
for i in range(100):
    readings.append(sensor.read())
""",
        "after": """# Efficient: Pre-allocated list
from micropython import const
MAX_READINGS = const(100)
readings = [None] * MAX_READINGS

for i in range(MAX_READINGS):
    readings[i] = sensor.read()
""",
        "savings": "Eliminates heap fragmentation, ~20% faster"
    },

    "const_values": {
        "before": """# Inefficient: Constants use RAM
SENSOR_ADDR = 0x48
BUFFER_SIZE = 64
TIMEOUT_MS = 1000
""",
        "after": """# Efficient: Constants in flash
from micropython import const
SENSOR_ADDR = const(0x48)
BUFFER_SIZE = const(64)
TIMEOUT_MS = const(1000)
""",
        "savings": "4-8 bytes per constant"
    },

    "read_into": {
        "before": """# Inefficient: Allocates new buffer
with open("data.bin", "rb") as f:
    data = f.read()
    process(data)
""",
        "after": """# Efficient: Pre-allocated buffer
from micropython import const
MAX_FILE_SIZE = const(512)
buffer = bytearray(MAX_FILE_SIZE)

with open("data.bin", "rb") as f:
    bytes_read = f.readinto(buffer)
    process(buffer[:bytes_read])
""",
        "savings": "Eliminates allocation, reusable buffer"
    },

    "bytes_vs_string": {
        "before": """# Inefficient: String operations
command = "AT+CMD="
command = command + str(value)
uart.write(command)
""",
        "after": """# Efficient: Bytes operations
from micropython import const
CMD_PREFIX = b"AT+CMD="
buffer = bytearray(20)
buffer[0:len(CMD_PREFIX)] = CMD_PREFIX
value_bytes = str(value).encode()
buffer[len(CMD_PREFIX):len(CMD_PREFIX)+len(value_bytes)] = value_bytes
uart.write(buffer[:len(CMD_PREFIX)+len(value_bytes)])
""",
        "savings": "No string allocations"
    },

    "struct_pack": {
        "before": """# Inefficient: Manual byte packing
data = bytearray(4)
data[0] = (value >> 24) & 0xFF
data[1] = (value >> 16) & 0xFF
data[2] = (value >> 8) & 0xFF
data[3] = value & 0xFF
""",
        "after": """# Efficient: struct.pack_into
import struct
data = bytearray(4)
struct.pack_into(">I", data, 0, value)
""",
        "savings": "More compact, less error-prone"
    }
}


def print_optimization_templates():
    """Display all optimization templates."""
    print("CircuitPython Memory Optimization Templates")
    print("=" * 70)

    for name, template in OPTIMIZATION_TEMPLATES.items():
        print(f"\n{'='*70}")
        print(f"Optimization: {name.replace('_', ' ').title()}")
        print(f"Savings: {template['savings']}")
        print('-' * 70)
        print(template['before'])
        print('-' * 70)
        print(template['after'])


if __name__ == "__main__":
    print_optimization_templates()
