@echo off
echo [*] Installing PyInstaller...
pip install pyinstaller

echo [*] Compiling SubVigil as a single binary with no CMD popup...
python -m PyInstaller --noconfirm --onefile --windowed --name "SubVigil" ^
    --add-data "modules;modules" ^
    --add-data "ai_engine;ai_engine" ^
    --icon "ico.ico" ^
    main.py

echo [*] Build complete! Check the 'dist' folder for SubVigil.exe.
pause