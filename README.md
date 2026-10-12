# Agentic-Security-bug-hunter

**Discover, patch, and verify vulnerabilities in C/C++ code.**

CRS is an experimental security tool that combines **static analysis, fuzzing, and LLM-assisted patch generation** into a single workflow. Instead of stopping at a vulnerability report, it attempts a source-code fix and tests whether that fix holds up.

The current implementation is a **single-target prototype**, focused on C/C++ memory-safety bugs.

## What CRS Does

- **Discover vulnerabilities** using Semgrep for static analysis and libFuzzer with AddressSanitizer (ASan) for runtime crashes.
- **Correlate evidence** by mapping analyzer observations to source files, functions, and lines, producing unified findings where they match.
- **Generate patches** using an LLM to propose source changes as unified diffs.
- **Validate changes** with Git before applying a candidate patch.
- **Verify fixes** through regression tests, crash reproduction, and bounded fuzzing. Failed fixes are rolled back, and the system can retry with failure feedback.

## Workflow

```text
C/C++ Target
     ↓
Semgrep + libFuzzer / ASan
     ↓
Findings & evidence
     ↓
LLM-generated patch
     ↓
Git validation & application
     ↓
Regression tests + crash replay + fuzzing
     ↓
Accept fix / Roll back & retry
```

## Built With

**Python** · **C/C++** · **Semgrep** · **LLVM/libFuzzer** · **AddressSanitizer** · **Git** · **Gemini API**

## Project Status

The core discovery → patch → verification pipeline is working on controlled targets. The current mapper handles Semgrep findings and matching Semgrep/libFuzzer observations.

The next development stages are **automatic target discovery**, **fuzz-harness generation**, and eventually **multi-file repository analysis**.

> **Note:** CRS is a research prototype, not a production vulnerability scanner. Use it only on software you own or are authorized to test.