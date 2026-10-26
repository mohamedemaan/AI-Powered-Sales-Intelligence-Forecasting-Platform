@echo off
echo ======================================================================
echo   Sales Intel AI Platform — Automated Backend Test Suite Runner
echo ======================================================================
cd backend
if exist ".venv\Scripts\python.exe" (
    .venv\Scripts\python.exe run_tests.py
) else (
    python run_tests.py
)
cd ..

