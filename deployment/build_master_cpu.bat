@echo off
echo ========================================================
echo   Master Physics Analyzer Build Script (CPU ONLY)
echo ========================================================

IF NOT EXIST "..\.venv_cpu" (
    echo [INFO] Creating an isolated CPU-only virtual environment...
    python -m venv ..\.venv_cpu
    ..\.venv_cpu\Scripts\python.exe -m pip install numpy scipy numba numexpr matplotlib pyinstaller
) ELSE (
    echo [INFO] Isolated .venv_cpu already exists. Skipping creation.
)

echo.
echo [INFO] Staging pure python source code...
..\.venv_cpu\Scripts\python.exe build_staged.py

echo.
echo [INFO] Building CPU-Only Master Physics Analyzer...
echo.

..\.venv_cpu\Scripts\pyinstaller.exe --onefile ^
  --name "Physics_Analyzer_CPU" ^
  --exclude-module cupy ^
  --exclude-module numba.cuda ^
  --collect-all numba ^
  --hidden-import numexpr ^
  --hidden-import numpy ^
  --hidden-import scipy.fft ^
  --hidden-import scipy.integrate ^
  --add-data "staging\self_energy;self_energy" ^
  --add-data "staging\susceptibility;susceptibility" ^
  staging\master_app_cpu.py

echo.
echo [INFO] Cleaning up temporary build files...
del /Q *.spec
rmdir /S /Q staging

echo.
echo [SUCCESS] Build Complete! You can find Physics_Analyzer_CPU.exe in the deployment/dist folder.
pause
