import os
from nicegui import ui
from broh5.lib.interactions import GuiInteraction


def main():
    GuiInteraction()
    os.environ["NO_NETIFACES"] = "True"
    ui.run(reload=False, title="Browser-based Hdf Viewer", port=8110)


if __name__ in {"__main__", "__mp_main__"}:
    main()

