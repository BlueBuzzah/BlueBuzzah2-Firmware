#!/usr/bin/env python3
"""
CircuitPython Memory Profiler
Analyzes source code for memory waste patterns on nRF52840.
"""

import re
import sys
import argparse
from pathlib import Path
from typing import List, Dict, Any

try:
    from patterns import MEMORY_PATTERNS
    from import_costs import IMPORT_COSTS
except ImportError:
    MEMORY_PATTERNS = []
    IMPORT_COSTS = {}


class MemoryProfiler:
    """Static analysis for CircuitPython memory usage."""

    def __init__(self, source_file: str):
        self.file_path = Path(source_file)
        with open(source_file, 'r') as f:
            self.source = f.read()
        self.lines = self.source.split('\n')
        self.issues = []
        self.import_cost = 0
        self.unused_imports = []

    def analyze(self) -> Dict[str, Any]:
        """Run all analysis checks."""
        self._analyze_imports()
        self._detect_patterns()
        self._check_const_usage()
        self._estimate_peak_memory()

        return {
            "summary": {
                "estimated_peak_memory": self.peak_memory,
                "gc_pressure": self._calculate_gc_pressure(),
                "fragmentation_risk": self._assess_fragmentation(),
                "available_memory": 131072 - self.import_cost - self.peak_memory,
            },
            "critical_issues": sorted(self.issues, key=lambda x: x.get('priority', 0), reverse=True),
            "import_analysis": {
                "total_cost": self.import_cost,
                "unused_imports": self.unused_imports,
                "breakdown": self.import_breakdown
            }
        }

    def _analyze_imports(self):
        """Detect imports and calculate memory cost."""
        import_pattern = re.compile(r'^(?:from\s+(\S+)|import\s+(\S+))', re.MULTILINE)
        imports_found = set()
        self.import_breakdown = {}

        for match in import_pattern.finditer(self.source):
            module = match.group(1) or match.group(2)
            module_base = module.split('.')[0]
            imports_found.add(module_base)

            cost = IMPORT_COSTS.get(module_base, 0)
            self.import_breakdown[module_base] = cost
            self.import_cost += cost

        # Simple heuristic: if imported but never referenced, mark as unused
        for module in imports_found:
            if self.source.count(module) == 1:  # Only appears in import line
                self.unused_imports.append(module)
                self.issues.append({
                    "line": self._find_import_line(module),
                    "code": f"import {module}",
                    "issue": f"Unused import '{module}'",
                    "memory_waste": f"{IMPORT_COSTS.get(module, 0)} bytes",
                    "fix": f"Remove import to save {IMPORT_COSTS.get(module, 0)} bytes",
                    "severity": "HIGH" if IMPORT_COSTS.get(module, 0) > 4096 else "MEDIUM",
                    "priority": IMPORT_COSTS.get(module, 0)
                })

    def _find_import_line(self, module: str) -> int:
        """Find line number of import statement."""
        for i, line in enumerate(self.lines, 1):
            if module in line and ('import' in line):
                return i
        return 0

    def _detect_patterns(self):
        """Scan for known memory waste patterns."""
        for pattern_def in MEMORY_PATTERNS:
            regex = re.compile(pattern_def['pattern'])
            for i, line in enumerate(self.lines, 1):
                if regex.search(line):
                    self.issues.append({
                        "line": i,
                        "code": line.strip(),
                        "issue": pattern_def['issue'],
                        "fix": pattern_def['fix'],
                        "severity": pattern_def['severity'],
                        "memory_waste": pattern_def.get('memory_impact', 'Unknown'),
                        "priority": self._severity_to_priority(pattern_def['severity'])
                    })

    def _check_const_usage(self):
        """Find numeric/string constants that should use const()."""
        # Look for UPPER_CASE = numeric_value without const()
        const_pattern = re.compile(r'^([A-Z_]+)\s*=\s*(\d+|0x[0-9a-fA-F]+)', re.MULTILINE)

        # Check if micropython.const is imported
        has_const_import = 'from micropython import const' in self.source

        for match in const_pattern.finditer(self.source):
            var_name = match.group(1)
            if not has_const_import or not re.search(rf'{var_name}\s*=\s*const\(', self.source):
                line_num = self.source[:match.start()].count('\n') + 1
                self.issues.append({
                    "line": line_num,
                    "code": match.group(0),
                    "issue": f"Constant '{var_name}' uses RAM instead of flash",
                    "fix": f"Use: from micropython import const; {var_name} = const({match.group(2)})",
                    "severity": "LOW",
                    "memory_waste": "4-8 bytes per constant",
                    "priority": 10
                })

    def _estimate_peak_memory(self):
        """Rough estimate of peak memory usage."""
        # Very simple heuristic based on allocations
        allocations = self.source.count('=')  # Assignment is potential allocation
        loops = len(re.findall(r'\b(for|while)\b', self.source))

        # Base estimate: 100 bytes per allocation, 500 extra per loop
        self.peak_memory = (allocations * 100) + (loops * 500) + self.import_cost

    def _calculate_gc_pressure(self) -> str:
        """Estimate garbage collection pressure."""
        allocations_in_loops = 0
        in_loop = False
        indent_level = 0

        for line in self.lines:
            stripped = line.lstrip()
            current_indent = len(line) - len(stripped)

            if re.match(r'(for|while)\b', stripped):
                in_loop = True
                indent_level = current_indent
            elif in_loop and current_indent <= indent_level and stripped:
                in_loop = False

            if in_loop and '=' in stripped:
                allocations_in_loops += 1

        if allocations_in_loops > 10:
            return "HIGH"
        elif allocations_in_loops > 3:
            return "MEDIUM"
        return "LOW"

    def _assess_fragmentation(self) -> str:
        """Estimate memory fragmentation risk."""
        string_ops = len(re.findall(r'\+.*["\']|["\'].*\+', self.source))
        list_appends = self.source.count('.append(')

        risk_score = string_ops + (list_appends * 2)

        if risk_score > 15:
            return "HIGH"
        elif risk_score > 5:
            return "MEDIUM"
        return "LOW"

    def _severity_to_priority(self, severity: str) -> int:
        """Convert severity to numeric priority."""
        return {"HIGH": 100, "MEDIUM": 50, "LOW": 10}.get(severity, 0)


def print_report(report: Dict[str, Any], show_suggestions: bool = True):
    """Format and print analysis report."""
    print("\n" + "="*60)
    print("CircuitPython Memory Profile")
    print("="*60)

    summary = report['summary']
    print(f"\nEstimated peak memory: {summary['estimated_peak_memory']:,} bytes")
    print(f"Available memory: {summary['available_memory']:,} bytes")
    print(f"Margin: {summary['available_memory'] / 131072 * 100:.1f}%")
    print(f"GC pressure: {summary['gc_pressure']}")
    print(f"Fragmentation risk: {summary['fragmentation_risk']}")

    imports = report['import_analysis']
    print(f"\nImport costs: {imports['total_cost']:,} bytes")
    for module, cost in imports['breakdown'].items():
        unused = " [UNUSED]" if module in imports['unused_imports'] else ""
        print(f"  {module}: {cost:,} bytes{unused}")

    issues = report['critical_issues']
    print(f"\n{'='*60}")
    print(f"Critical Issues Found: {len(issues)}")
    print("="*60)

    for i, issue in enumerate(issues[:10], 1):  # Show top 10
        print(f"\n{i}. Line {issue['line']}: {issue['issue']}")
        print(f"   Code: {issue['code'][:60]}")
        print(f"   Impact: {issue['memory_waste']}")
        if show_suggestions:
            print(f"   Fix: {issue['fix'][:70]}")


def main():
    parser = argparse.ArgumentParser(description="Profile CircuitPython memory usage")
    parser.add_argument("file", help="Python file to analyze")
    parser.add_argument("--suggest", action="store_true", help="Show optimization suggestions")
    parser.add_argument("--runtime", action="store_true", help="Generate instrumented code for runtime profiling")

    args = parser.parse_args()

    if not Path(args.file).exists():
        print(f"Error: File '{args.file}' not found")
        sys.exit(1)

    profiler = MemoryProfiler(args.file)
    report = profiler.analyze()

    print_report(report, show_suggestions=args.suggest)

    if args.runtime:
        print("\nRuntime profiling not yet implemented")
        print("See examples/measure_imports.py for manual instrumentation")


if __name__ == "__main__":
    main()
