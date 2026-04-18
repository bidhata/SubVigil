"""
SubGrab entry point.

  Double-click / no args  →  GUI
  SubGrab.exe domain ...  →  CLI (same interface as subgrab.py)
"""
import sys


def _hide_console():
    try:
        import ctypes
        ctypes.windll.user32.ShowWindow(
            ctypes.windll.kernel32.GetConsoleWindow(), 0)
    except Exception:
        pass


def main():
    args = sys.argv[1:]
    if not args or args[0] == "--gui":
        _hide_console()
        from subgrab_gui import main as gui_main
        gui_main()
    else:
        from subgrab import main as cli_main
        cli_main()


if __name__ == "__main__":
    main()
