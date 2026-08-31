@echo off
echo ========================================================
echo   Master Physics Analyzer Build Script (GPU ^& CPU)
echo ========================================================
echo.

IF NOT EXIST "..\.venv" (
    echo [INFO] No .venv found in root. Creating a unified virtual environment...
    python -m venv ..\.venv
    echo [INFO] Installing required dependencies...
    ..\.venv\Scripts\python.exe -m pip install --upgrade pip
    ..\.venv\Scripts\python.exe -m pip install numpy scipy numba numexpr matplotlib pyinstaller
    ..\.venv\Scripts\python.exe -m pip install cupy-cuda12x -f https://pip.cupy.dev/pre
) ELSE (
    echo [INFO] Unified .venv found.
    ..\.venv\Scripts\python.exe -m pip install numexpr
)

echo.
echo [INFO] Staging pure python source code...
..\.venv\Scripts\python.exe build_staged.py

echo.
echo [INFO] Bundling CuPy and Numba CUDA dependencies...
echo.

..\.venv\Scripts\pyinstaller.exe --onefile ^
  --name "Physics_Analyzer" ^
  --collect-all numba ^
  --hidden-import numpy ^
  --hidden-import scipy.fft ^
  --hidden-import scipy.integrate ^
  --hidden-import numexpr ^
  --hidden-import cupy ^
  --add-data "staging\self_energy;self_energy" ^
  --add-data "staging\susceptibility;susceptibility" ^
  --add-data "..\.venv\Lib\site-packages\nvidia\cublas\bin\cublas64_12.dll;cupy\.data\lib" ^
  --add-data "..\.venv\Lib\site-packages\nvidia\cuda_runtime\bin\cudart64_12.dll;cupy\.data\lib" ^
  --add-data "..\.venv\Lib\site-packages\nvidia\cufft\bin\cufft64_11.dll;cupy\.data\lib" ^
  --add-data "..\.venv\Lib\site-packages\nvidia\curand\bin\curand64_10.dll;cupy\.data\lib" ^
  --add-data "..\.venv\Lib\site-packages\nvidia\cuda_nvrtc\bin\nvrtc64_120_0.dll;cupy\.data\lib" ^
  --add-data "..\.venv\Lib\site-packages\nvidia\cuda_nvrtc\bin\nvrtc-builtins64_129.dll;cupy\.data\lib" ^
  --add-data "..\.venv\Lib\site-packages\nvidia\nvjitlink\bin\nvJitLink_120_0.dll;cupy\.data\lib" ^
  --add-data "..\.venv\Lib\site-packages\nvidia\cuda_nvcc\nvvm\bin\nvvm64_40_0.dll;cuda_toolkit\nvvm\bin" ^
  --add-data "..\.venv\Lib\site-packages\nvidia\cuda_nvcc\nvvm\libdevice\libdevice.10.bc;cuda_toolkit\nvvm\libdevice" ^
  --add-data "..\.venv\Lib\site-packages\nvidia\cuda_runtime\bin\cudart64_12.dll;cuda_toolkit\bin" ^
  --add-data "..\.venv\Lib\site-packages\nvidia\cuda_nvrtc\bin\nvrtc64_120_0.dll;cuda_toolkit\bin" ^
  --add-data "..\.venv\Lib\site-packages\nvidia\cuda_nvrtc\bin\nvrtc-builtins64_129.dll;cuda_toolkit\bin" ^
  staging\master_app.py

echo.
echo [INFO] Cleaning up temporary build files...
del /Q *.spec
rmdir /S /Q staging

echo.
echo [SUCCESS] Build Complete! You can find Physics_Analyzer.exe in the deployment/dist folder.
pause
