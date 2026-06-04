@echo off
echo [*] Installing PyInstaller...
pip install pyinstaller

echo [*] Compiling SubGrab as a single binary with no CMD popup...
python -m PyInstaller --noconfirm --onefile --windowed --name "SubGrab" ^
    --add-data "modules;modules" ^
    --add-data "ai_engine;ai_engine" ^
    main.py

echo [*] Build complete! Check the 'dist' folder for SubGrab.exe.
pause