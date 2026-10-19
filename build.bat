@echo off
REM ---------------------------------------------------------------------------
REM SubVigil Windows build script. Must be run on Windows (PyInstaller does not
REM cross-compile). Produces dist\SubVigil.exe.
REM ---------------------------------------------------------------------------

echo [*] Installing dependencies...
pip install -r requirements.txt
pip install pyinstaller

echo [*] Building SubVigil.exe from SubVigil.spec (one-file, no console popup)...
python -m PyInstaller --noconfirm --clean SubVigil.spec
if errorlevel 1 (
    echo [!] Build failed.
    pause
    exit /b 1
)

echo [*] Build complete! Check the 'dist' folder for SubVigil.exe.
pause
