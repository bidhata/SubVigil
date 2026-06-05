import sys

def main():
    # If arguments are passed (e.g. from the GUI subprocess or CLI), route to CLI
    if len(sys.argv) > 1:
        import subvigil
        subvigil.main()
    else:
        # No arguments passed, launch the GUI
        import subvigil_gui
        subvigil_gui.main()

if __name__ == "__main__":
    main()