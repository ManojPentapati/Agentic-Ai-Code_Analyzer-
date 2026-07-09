"""
Agent tools for the Agentic AI Code Analyzer.

Provides functional tools that agents can invoke to gather
structured data about the user's code before generating analysis.
"""

import re

# pyrefly: ignore [missing-import]
from langchain.tools import tool


# ──────────────────────────────────────────────
# Language Detection
# ──────────────────────────────────────────────

LANGUAGE_SIGNATURES: dict[str, list[str]] = {
    "python": [
        r"\bdef\s+\w+\s*\(", r"\bimport\s+\w+", r"\bclass\s+\w+.*:",
        r"\bprint\s*\(", r"\bself\b", r"\bif\s+__name__\s*==",
        r"^\s*@\w+", r"\blambda\b", r"\bwith\s+\w+",
    ],
    "javascript": [
        r"\bconst\s+\w+", r"\blet\s+\w+", r"\bfunction\s+\w+",
        r"\bconsole\.log\b", r"=>\s*\{", r"\brequire\s*\(",
        r"\bmodule\.exports\b", r"\basync\s+function\b",
    ],
    "typescript": [
        r"\binterface\s+\w+", r":\s*(string|number|boolean|any)\b",
        r"\btype\s+\w+\s*=", r"\benum\s+\w+", r"\bas\s+\w+",
    ],
    "java": [
        r"\bpublic\s+(static\s+)?void\b", r"\bSystem\.out\.print",
        r"\bclass\s+\w+\s*(extends|implements)\b",
        r"\bimport\s+java\.", r"\bnew\s+\w+\s*\(",
    ],
    "c++": [
        r"#include\s*<\w+>", r"\bstd::\w+", r"\bcout\s*<<",
        r"\bint\s+main\s*\(", r"\busing\s+namespace\b",
        r"\btemplate\s*<", r"\bvector\s*<",
    ],
    "c": [
        r"#include\s*<\w+\.h>", r"\bprintf\s*\(", r"\bmalloc\s*\(",
        r"\btypedef\s+struct\b", r"\bint\s+main\s*\(",
    ],
    "go": [
        r"\bfunc\s+\w+\s*\(", r"\bpackage\s+\w+", r"\bfmt\.\w+",
        r"\bgo\s+func\b", r":=\s*", r"\bdefer\s+\w+",
    ],
    "rust": [
        r"\bfn\s+\w+\s*\(", r"\blet\s+mut\s+", r"\bimpl\s+\w+",
        r"\bpub\s+(fn|struct|enum)\b", r"\bmatch\s+\w+",
        r"println!\s*\(", r"\bOption<\w+>",
    ],
    "sql": [
        r"\bSELECT\b.*\bFROM\b", r"\bINSERT\s+INTO\b",
        r"\bCREATE\s+TABLE\b", r"\bALTER\s+TABLE\b",
        r"\bWHERE\b", r"\bJOIN\b",
    ],
    "html": [
        r"<html", r"<div\b", r"<body\b", r"<!DOCTYPE\s+html>",
        r"<script\b", r"<link\b",
    ],
    "css": [
        r"\{[^}]*;\s*\}", r"\.\w+\s*\{", r"#\w+\s*\{",
        r"@media\s+", r"@import\s+",
    ],
}


@tool
def detect_language(code: str) -> str:
    """
    Auto-detect the programming language of a code snippet
    by matching against known syntax patterns.

    Args:
        code: The source code to analyze.

    Returns:
        Detected language name (e.g., 'python', 'javascript').
    """
    scores: dict[str, int] = {}

    for language, patterns in LANGUAGE_SIGNATURES.items():
        score = sum(
            1
            for pattern in patterns
            if re.search(pattern, code, re.MULTILINE | re.IGNORECASE)
        )
        if score > 0:
            scores[language] = score

    if not scores:
        return "unknown"

    return max(scores, key=scores.get)


# ──────────────────────────────────────────────
# Complexity Analysis
# ──────────────────────────────────────────────

@tool
def calculate_complexity(code: str) -> str:
    """
    Calculate a complexity score (0-100) for the given code based on
    lines of code, nesting depth, function count, and control flow.

    Args:
        code: The source code to analyze.

    Returns:
        A structured complexity report string.
    """
    lines = code.strip().split("\n")
    total_lines = len(lines)
    non_empty_lines = sum(1 for line in lines if line.strip())

    # Count functions / methods
    func_count = len(re.findall(
        r"\b(def|function|func|fn|void|public\s+static)\s+\w+\s*\(",
        code, re.MULTILINE,
    ))

    # Count control flow statements
    control_flow = len(re.findall(
        r"\b(if|else|elif|for|while|switch|case|try|catch|except|match)\b",
        code, re.MULTILINE,
    ))

    # Measure max nesting depth
    max_depth = 0
    current_depth = 0
    for char in code:
        if char in "({":
            current_depth += 1
            max_depth = max(max_depth, current_depth)
        elif char in ")}":
            current_depth = max(0, current_depth - 1)

    # Count classes
    class_count = len(re.findall(
        r"\b(class|struct|interface|enum)\s+\w+", code, re.MULTILINE,
    ))

    # Compute weighted score (0-100)
    score = min(100, (
        (min(total_lines, 200) / 200) * 25 +          # Lines (max 25)
        (min(func_count, 15) / 15) * 20 +               # Functions (max 20)
        (min(control_flow, 20) / 20) * 20 +              # Control flow (max 20)
        (min(max_depth, 10) / 10) * 20 +                 # Nesting (max 20)
        (min(class_count, 5) / 5) * 15                   # Classes (max 15)
    ))

    return (
        f"Complexity Score: {score:.0f}/100\n"
        f"Total Lines: {total_lines}\n"
        f"Non-empty Lines: {non_empty_lines}\n"
        f"Functions/Methods: {func_count}\n"
        f"Control Flow Statements: {control_flow}\n"
        f"Max Nesting Depth: {max_depth}\n"
        f"Classes/Structs: {class_count}"
    )


# ──────────────────────────────────────────────
# Security Scanner
# ──────────────────────────────────────────────

SECURITY_PATTERNS: list[tuple[str, str, str]] = [
    # (pattern, vulnerability_name, severity)
    (r"\beval\s*\(", "Use of eval()", "HIGH"),
    (r"\bexec\s*\(", "Use of exec()", "HIGH"),
    (r"\b(password|passwd|secret|api_key|token)\s*=\s*['\"]", "Hardcoded secret/credential", "CRITICAL"),
    (r"SELECT\s+.*\+.*\bfrom\b", "Potential SQL injection (string concatenation)", "HIGH"),
    (r"f['\"].*SELECT.*\{", "Potential SQL injection (f-string)", "HIGH"),
    (r"\bos\.system\s*\(", "Shell command execution via os.system()", "HIGH"),
    (r"\bsubprocess\.(call|run|Popen)\s*\(.*shell\s*=\s*True", "Shell injection risk (shell=True)", "HIGH"),
    (r"\bpickle\.loads?\s*\(", "Insecure deserialization (pickle)", "MEDIUM"),
    (r"\byaml\.load\s*\((?!.*Loader)", "Insecure YAML loading (no Loader specified)", "MEDIUM"),
    (r"\brandom\.(random|randint|choice)\b", "Weak randomness (use secrets module for crypto)", "LOW"),
    (r"# ?TODO|# ?FIXME|# ?HACK|# ?XXX", "Unresolved TODO/FIXME comment", "INFO"),
    (r"\bexcept\s*:\s*$", "Bare except clause (catches all exceptions)", "MEDIUM"),
    (r"chmod\s+777", "Overly permissive file permissions", "MEDIUM"),
    (r"verify\s*=\s*False", "SSL verification disabled", "HIGH"),
    (r"DEBUG\s*=\s*True", "Debug mode enabled in production", "MEDIUM"),
]


@tool
def scan_security_patterns(code: str) -> str:
    """
    Scan code for common security vulnerabilities, hardcoded secrets,
    injection risks, and unsafe patterns.

    Args:
        code: The source code to scan.

    Returns:
        A structured security report with findings.
    """
    findings: list[str] = []

    for pattern, vuln_name, severity in SECURITY_PATTERNS:
        matches = re.finditer(pattern, code, re.MULTILINE | re.IGNORECASE)
        for match in matches:
            # Find line number
            line_num = code[:match.start()].count("\n") + 1
            findings.append(
                f"[{severity}] Line {line_num}: {vuln_name}"
            )

    if not findings:
        return "[PASS] No security issues detected."

    # Group by severity
    severity_order = ["CRITICAL", "HIGH", "MEDIUM", "LOW", "INFO"]
    sorted_findings = sorted(
        findings,
        key=lambda f: severity_order.index(
            f.split("]")[0].strip("[")
        ),
    )

    report = f"[WARN] Found {len(sorted_findings)} security issue(s):\n\n"
    report += "\n".join(f"  - {f}" for f in sorted_findings)
    return report


# ──────────────────────────────────────────────
# Code Pattern Checker
# ──────────────────────────────────────────────

CODE_SMELL_PATTERNS: list[tuple[str, str]] = [
    (r"(.+)\n(\1\n){2,}", "Duplicate code block detected"),
    (r"def\s+\w+\s*\([^)]{100,}\)", "Function with too many parameters"),
    (r"if\s+.*\bTrue\b|if\s+.*\bFalse\b", "Redundant boolean comparison"),
    (r"\bprint\s*\(", "Debug print statement left in code"),
    (r"#\s*\w+.*\n\s*#\s*\w+.*\n\s*#\s*\w+.*\n\s*#\s*\w+", "Excessive inline comments (consider docstrings)"),
    (r"except\s+Exception\s+as\s+\w+:\s*\n\s*pass", "Exception silently swallowed"),
    (r"from\s+\w+\s+import\s+\*", "Wildcard import (pollutes namespace)"),
    (r"global\s+\w+", "Use of global variable"),
    (r"time\.sleep\s*\(\s*\d{2,}\s*\)", "Long sleep/delay in code"),
]


@tool
def check_code_patterns(code: str) -> str:
    """
    Detect anti-patterns, code smells, and style issues in the code.

    Args:
        code: The source code to check.

    Returns:
        A report of detected code smells and anti-patterns.
    """
    issues: list[str] = []

    for pattern, description in CODE_SMELL_PATTERNS:
        matches = list(re.finditer(pattern, code, re.MULTILINE))
        if matches:
            line_nums = [
                code[:m.start()].count("\n") + 1 for m in matches
            ]
            lines_str = ", ".join(str(n) for n in line_nums[:5])
            suffix = f" (+{len(line_nums) - 5} more)" if len(line_nums) > 5 else ""
            issues.append(f"  - {description} (line {lines_str}{suffix})")

    # Check line length
    long_lines = [
        i + 1 for i, line in enumerate(code.split("\n"))
        if len(line) > 120
    ]
    if long_lines:
        count = len(long_lines)
        issues.append(f"  - {count} line(s) exceed 120 characters")

    if not issues:
        return "[PASS] No code smells or anti-patterns detected."

    report = f"[INFO] Found {len(issues)} code quality issue(s):\n\n"
    report += "\n".join(issues)
    return report


# ──────────────────────────────────────────────
# Tool Registry
# ──────────────────────────────────────────────

ALL_TOOLS = [
    detect_language,
    calculate_complexity,
    scan_security_patterns,
    check_code_patterns,
]
