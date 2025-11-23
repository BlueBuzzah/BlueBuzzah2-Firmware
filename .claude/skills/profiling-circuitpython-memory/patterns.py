"""
Memory waste pattern database for CircuitPython on nRF52840.
Each pattern includes detection regex, description, and fix suggestion.
"""

MEMORY_PATTERNS = [
    {
        "pattern": r'(\w+)\s*=\s*\1\s*\+\s*["\']',
        "issue": "String concatenation creates new string objects",
        "fix": "Use bytearray or pre-allocated buffer",
        "severity": "HIGH",
        "memory_impact": "~2x string size per operation"
    },
    {
        "pattern": r'(\w+)\s*=\s*\1\s*\+\s*str\(',
        "issue": "String concatenation with str() in potential loop",
        "fix": "Pre-allocate bytearray, use struct.pack_into() for numbers",
        "severity": "HIGH",
        "memory_impact": "~100-500 bytes per operation"
    },
    {
        "pattern": r'\.append\(',
        "issue": "List growth via append() fragments heap",
        "fix": "Pre-allocate list with [None] * size, then assign by index",
        "severity": "HIGH",
        "memory_impact": "Varies, causes fragmentation"
    },
    {
        "pattern": r'f["\'].*\{.*\}',
        "issue": "F-string formatting allocates temporary strings",
        "fix": "Use .format() only when necessary, prefer bytes operations",
        "severity": "MEDIUM",
        "memory_impact": "~50-200 bytes per format"
    },
    {
        "pattern": r'\.format\(',
        "issue": "String formatting creates new string objects",
        "fix": "Minimize in loops, use bytes/bytearray for repeated operations",
        "severity": "MEDIUM",
        "memory_impact": "~50-200 bytes per call"
    },
    {
        "pattern": r'\blist\(',
        "issue": "list() constructor allocates new list",
        "fix": "Pre-allocate if size known, or use generator/iterator",
        "severity": "MEDIUM",
        "memory_impact": "24 bytes + 8 bytes per element"
    },
    {
        "pattern": r'\bdict\(',
        "issue": "dict() constructor allocates hash table",
        "fix": "Use literal {} or minimize dict size, consider namedtuple",
        "severity": "MEDIUM",
        "memory_impact": "~240 bytes + 24 bytes per entry"
    },
    {
        "pattern": r'\bset\(',
        "issue": "set() allocates hash table structure",
        "fix": "Use list or tuple if ordering acceptable, minimize size",
        "severity": "MEDIUM",
        "memory_impact": "~240 bytes + overhead per element"
    },
    {
        "pattern": r'range\(\w+\)',
        "issue": "range() with variable may allocate (in some contexts)",
        "fix": "Use range with const() argument where possible",
        "severity": "LOW",
        "memory_impact": "Usually minimal, iterator-based"
    },
    {
        "pattern": r'\w+\s*=\s*\[.*\]\s*\*\s*\w+',
        "issue": "List multiplication with variable size",
        "fix": "Ensure multiplier is const() to optimize allocation",
        "severity": "LOW",
        "memory_impact": "Depends on size"
    },
    {
        "pattern": r'\.split\(',
        "issue": "String split() creates multiple new string objects",
        "fix": "Process bytes directly with find() if possible",
        "severity": "MEDIUM",
        "memory_impact": "~50 bytes + size of each substring"
    },
    {
        "pattern": r'\.join\(',
        "issue": "String join() creates new concatenated string",
        "fix": "Acceptable for one-time use, avoid in loops",
        "severity": "LOW",
        "memory_impact": "~total size of joined strings"
    },
    {
        "pattern": r'\.strip\(|\.lstrip\(|\.rstrip\(',
        "issue": "String strip operations create new string",
        "fix": "Acceptable for one-time parsing, avoid in loops",
        "severity": "LOW",
        "memory_impact": "~size of original string"
    },
    {
        "pattern": r'\.replace\(',
        "issue": "String replace() creates new string object",
        "fix": "Use bytearray with manual replacement for loops",
        "severity": "MEDIUM",
        "memory_impact": "~size of resulting string"
    },
    {
        "pattern": r'\bbytearray\(\w+\)',
        "issue": "bytearray() with variable size (verify not in loop)",
        "fix": "Ensure allocation happens once, outside loops",
        "severity": "MEDIUM",
        "memory_impact": "Size of array"
    },
    {
        "pattern": r'(\[\]|\{\})\s*$',
        "issue": "Empty list/dict initialization (might be grown later)",
        "fix": "Pre-allocate if final size known",
        "severity": "LOW",
        "memory_impact": "Minimal initially, grows if append/insert used"
    },
    {
        "pattern": r'import\s+json',
        "issue": "json module uses significant memory for parsing",
        "fix": "Use ujson if available, or manual parsing for simple data",
        "severity": "MEDIUM",
        "memory_impact": "~2000-5000 bytes base + parsed data"
    },
    {
        "pattern": r'import\s+re\b',
        "issue": "re module (regex) uses memory for pattern compilation",
        "fix": "Use simple string methods (find, startswith) where possible",
        "severity": "MEDIUM",
        "memory_impact": "~1500 bytes base + compiled patterns"
    },
    {
        "pattern": r'\bprint\(.*\+.*\)',
        "issue": "String concatenation in print() allocates temporary",
        "fix": "Use print(a, b, c) with comma separation instead",
        "severity": "LOW",
        "memory_impact": "~size of concatenated string"
    },
    {
        "pattern": r'\*\*',
        "issue": "Dictionary unpacking or exponentiation (check context)",
        "fix": "If dict unpacking, ensure minimal allocations",
        "severity": "LOW",
        "memory_impact": "Varies"
    },
    {
        "pattern": r'\bmap\(|\bfilter\(',
        "issue": "map/filter create iterator objects",
        "fix": "Usually fine, but verify memory if processing large data",
        "severity": "LOW",
        "memory_impact": "Iterator overhead minimal"
    },
    {
        "pattern": r'\[.*for.*in.*\]',
        "issue": "List comprehension allocates list immediately",
        "fix": "Use generator expression (parentheses) if iterating once",
        "severity": "MEDIUM",
        "memory_impact": "Full list size allocated at once"
    },
    {
        "pattern": r'\{.*for.*in.*\}',
        "issue": "Dict/set comprehension allocates collection immediately",
        "fix": "Consider building incrementally if memory-constrained",
        "severity": "MEDIUM",
        "memory_impact": "Full collection allocated at once"
    },
    {
        "pattern": r'\.read\(\)',
        "issue": "File/stream read() may allocate large buffer",
        "fix": "Use read_into(buffer) with pre-allocated bytearray",
        "severity": "HIGH",
        "memory_impact": "Size of data read"
    },
    {
        "pattern": r'try:.*except\s+Exception',
        "issue": "Broad exception catching (not memory issue, but pattern check)",
        "fix": "Catch specific exceptions for clarity",
        "severity": "LOW",
        "memory_impact": "None (code quality issue)"
    }
]


# Severity levels:
# HIGH: Almost always causes memory issues in typical CircuitPython usage
# MEDIUM: Problematic in loops or with large data
# LOW: Minor issue or depends heavily on context

def get_patterns_by_severity(severity: str):
    """Get all patterns matching a severity level."""
    return [p for p in MEMORY_PATTERNS if p['severity'] == severity]


def get_high_priority_patterns():
    """Get patterns that should always be checked."""
    return get_patterns_by_severity('HIGH')
