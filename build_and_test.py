import os
import sys
import subprocess

def main():
    print("========================================")
    print("🚀 BUILDING THE SALES INTELLIGENCE PLATFORM")
    print("========================================")

    # 1. Run all scaffolding scripts sequentially
    scripts = [
        "scaffold.py",
        "scaffold_phase2.py",
        "scaffold_phase3.py",
        "scaffold_phase4.py",
        "scaffold_phase5.py",
        "scaffold_phase6.py",
        "scaffold_phase8.py",
        "scaffold_phase9.py",
        "scaffold_phase10.py"
    ]

    for script in scripts:
        if os.path.exists(script):
            print(f"\n---> Executing {script}...")
            # We use exec to run them in the current python process
            with open(script, 'r', encoding='utf-8') as f:
                exec(f.read(), globals())
        else:
            print(f"\n[WARNING] {script} not found. Skipping.")

    print("\n✅ All project files generated successfully!\n")

    # 2. Check if Pytest is installed
    try:
        import pytest
    except ImportError:
        print("⚠️ 'pytest' is not installed in your current environment.")
        print("Please install backend dependencies to run tests:")
        print("   cd backend && pip install -r requirements.txt")
        return

    # 3. Run Backend Tests
    print("========================================")
    print("🧪 RUNNING BACKEND TESTS (PYTEST)")
    print("========================================")
    
    # We navigate to the backend directory context for the test
    os.chdir("backend")
    
    # Run pytest programmatically
    exit_code = pytest.main(["tests/"])
    
    if exit_code == 0:
        print("\n✅ Backend Tests Passed Successfully!")
    else:
        print(f"\n❌ Backend Tests Failed with exit code {exit_code}")

if __name__ == "__main__":
    main()
