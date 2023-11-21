import os
import argparse
from nicegui import ui
from broh5.lib.interactions import GuiInteraction
from broh5 import __version__


display_msg = """
===============================================================================

Web-browser-based GUI (Graphical User Interface) software for viewing HDF files

===============================================================================

Type: broh5 to run the software
Exit the software by pressing: Ctrl + C

===============================================================================
"""


def parse_args():
    parser = argparse.ArgumentParser(description=display_msg,
                                     formatter_class=
                                     argparse.RawDescriptionHelpFormatter)
    parser.add_argument('--version', action='version',
                        version=f'%(prog)s {__version__}')
    parser.parse_args()


def main():
    parse_args()
    GuiInteraction()
    os.environ["NO_NETIFACES"] = "True"
    ui.run(reload=False, title="Browser-based Hdf Viewer", port=8110)


if __name__ in {"__main__", "__mp_main__"}:
    main()

