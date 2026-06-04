import sys

def main():
    # If arguments are passed (e.g. from the GUI subprocess or CLI), route to CLI
    if len(sys.argv) > 1:
        import subgrab
        subgrab.main()
    else:
        # No arguments passed, launch the GUI
        import subgrab_gui
        subgrab_gui.main()

if __name__ == "__main__":
    main()