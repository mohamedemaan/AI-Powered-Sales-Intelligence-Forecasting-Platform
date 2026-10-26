"""
Sales Intel AI Platform — Automated Backend Test Runner
Executes all unit and integration test suites:
  - tests/test_analytics.py
  - tests/test_ml.py
  - tests/test_reporting.py
  - tests/test_audit_fixes.py
"""
import sys
import os

# Add backend directory to sys.path
backend_dir = os.path.dirname(os.path.abspath(__file__))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

try:
    import pytest
except ImportError:
    print("[ERROR] pytest is not installed in your current Python environment.")
    print("Please install requirements: pip install -r requirements.txt")
    sys.exit(1)

if __name__ == "__main__":
    print("=" * 70)
    print("  Sales Intel AI Platform — Executing Backend Test Suite")
    print("=" * 70)
    args = ["-v", os.path.join(backend_dir, "tests")] + sys.argv[1:]
    exit_code = pytest.main(args)
    sys.exit(exit_code)

