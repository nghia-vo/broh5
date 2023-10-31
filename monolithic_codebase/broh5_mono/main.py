import os
import h5py
import numpy as np
from matplotlib import pyplot as plt
from nicegui import ui
from nicegui.events import ValueChangeEventArguments
from broh5_mono.util.components import FilePicker, FileSaver
import broh5_mono.util.tools as tl

# ============================================================================
#                   Global parameters for the GUI
# ============================================================================

MARKER_LIST = [",", ".", "o", "x"]
CMAP_LIST = ["gray", "inferno", "afmhot", "viridis", "magma"]
AXIS_LIST = [0, 1, 2]
FONT_STYLE = "font-size: 105%; font-weight: bold"
DISPLAY_TYPE = ["plot", "table"]
UPDATE_RATE = 0.2  # s
DPI = 96
RATIO = 0.65  # Ratio for adjusting size between image/plot and screen
MAX_FIG_SIZE = [12.0, 9.0]
INPUT_EXT = ["hdf", "nxs", "h5"]
PLOT_COLOR = "blue"
HEADER_COLOR = "#3874c8"
HEADER_TITLE = "BROWSER-BASED HDF VIEWER"
LEFT_DRAWER_COLOR = "#d7e3f4"
TREE_BGR_COLOR = "#f8f8ff"


def main():
    # ========================================================================
    #                  Methods to be called by UI interactions
    # ========================================================================
    def show_key(event: ValueChangeEventArguments, file_path):
        """Show key to a dataset/group of a hdf file"""
        hdf_key = event.value
        if hdf_key is not None:
            hdf_key_display.set_text(hdf_key)
        else:
            hdf_value_display.set_text("")
        if file_path is not None:
            file_path_display.set_text(file_path)

    def disable_sliders():
        """Disable and reset values of sliders"""
        main_slider.set_value(0)
        main_slider.disable()
        min_slider.set_value(0)
        min_slider.disable()
        max_slider.set_value(255)
        max_slider.disable()

    def enable_ui_elements_3d_data():
        """
        Enable UI-elements for displaying a slice from 3d data as an image and
        disable non-related UI-elements.
        """
        # Enable ui-components related to image show
        main_slider.enable()
        max_slider.enable()
        min_slider.enable()
        main_plot.set_visibility(True)
        axis_list.enable()
        cmap_list.enable()
        save_image_button.enable()

        # Disable other ui-components
        main_table.set_visibility(False)
        display_type.disable()
        marker_list.disable()
        save_data_button.disable()
        global data_1d_2d
        data_1d_2d = None

    def enable_ui_elements_1d_2d_data():
        """
        Enable UI-elements for displaying 1d/2d data as a table or plot, and
        disable non-related UI-elements.
        """
        global image
        image = None
        # Disable ui-components related to image show
        disable_sliders()
        axis_list.value = AXIS_LIST[0]
        cmap_list.value = CMAP_LIST[0]
        axis_list.disable()
        cmap_list.disable()
        save_image_button.disable()

        # Enable other ui-components
        display_type.enable()
        marker_list.enable()
        save_data_button.enable()

    def reset(keep_display=False):
        """Reset status of UI-elements"""
        if not keep_display:
            hdf_key_display.set_text("")
            file_path_display.set_text("")
            hdf_value_display.set_text("")
        axis_list.value = AXIS_LIST[0]
        cmap_list.value = CMAP_LIST[0]
        display_type.value = DISPLAY_TYPE[0]
        marker_list.value = MARKER_LIST[0]
        axis_list.disable()
        cmap_list.disable()
        display_type.disable()
        marker_list.disable()
        disable_sliders()
        global rows, columns, image, data_1d_2d
        rows, columns = None, None
        image, data_1d_2d = None, None
        main_table.set_visibility(False)
        main_plot.set_visibility(True)
        save_image_button.disable()
        save_data_button.disable()

    def reset_min_max():
        """Reset minimum and maximum values of sliders"""
        min_slider.set_value(0)
        max_slider.set_value(255)

    def display_3d_data(data_obj):
        """Display a slice of 3d array as an image"""
        enable_ui_elements_3d_data()
        (depth, height, width) = data_obj.shape
        current_max = main_slider._props["max"]
        if int(axis_list.value) == 2:
            max_val = width - 1
        elif int(axis_list.value) == 1:
            max_val = height - 1
        else:
            max_val = depth - 1
        if current_max != max_val:
            main_slider._props["max"] = max_val
            main_slider.update()
        d_pos = int(main_slider.value)
        if d_pos > max_val:
            main_slider.set_value(max_val)
            d_pos = max_val
        global current_slice, image
        new_slice = (main_slider.value, axis_list.value,
                     file_path_display.text)
        if new_slice != current_slice or image is None:
            current_slice = new_slice
            if int(axis_list.value) == 2:
                if depth > 1000 and height > 1000:
                    ui.notify("Slicing along axis 2 is very time consuming!")
                    axis_list.value = 0
                    main_slider.set_value(0)
                    image = data_obj[0]
                else:
                    image = data_obj[:, :, d_pos]
            elif int(axis_list.value) == 1:
                if depth > 1000 and width > 1000:
                    ui.notify("Slicing along axis 1 can take time !")
                image = data_obj[:, d_pos, :]
            else:
                image = data_obj[d_pos]
        min_val, max_val = int(min_slider.value), int(max_slider.value)
        if min_val > 0 or max_val < 255:
            if min_val >= max_val:
                min_val = np.clip(max_val - 1, 0, 254)
                min_slider.set_value(min_val)
            nmin, nmax = np.min(image), np.max(image)
            if nmax != nmin:
                image1 = np.uint8(255.0 * (image - nmin) / (nmax - nmin))
                image1 = np.clip(image1, min_val, max_val)
            else:
                image1 = np.zeros(image.shape)
        else:
            image1 = np.copy(image)
        with main_plot:
            plt.clf()
            plt.imshow(image1, cmap=cmap_list.value)
            plt.tight_layout()
            main_plot.update()

    def display_1d_2d_data(data_obj, disp_type="plot"):
        """Display 1d/2d array as a table or plot"""
        enable_ui_elements_1d_2d_data()
        global data_1d_2d
        data_1d_2d = data_obj[:]
        if disp_type == "table":
            main_plot.set_visibility(False)
            main_table.set_visibility(True)
            global rows, columns
            rows, columns = tl.format_table_from_array(data_obj[:])
            if main_table.rows is None:
                main_table._props["rows"] = rows
            else:
                main_table.rows[:] = rows
            main_table.update()
        else:
            main_plot.set_visibility(True)
            main_table.set_visibility(False)
            x, y = None, None
            img = False
            if len(data_obj.shape) == 2:
                (height, width) = data_obj.shape
                if height == 2:
                    x, y = np.asarray(data_obj[0]), np.asarray(data_obj[1])
                elif width == 2:
                    x = np.asarray(data_obj[:, 0])
                    y = np.asarray(data_obj[:, 1])
                else:
                    img = True
            else:
                size = len(data_obj)
                x, y = np.arange(size), np.asarray(data_obj[:])
            if x is not None:
                with main_plot:
                    plt.clf()
                    title = hdf_key_display.text.split("/")[-1]
                    plt.title(title.capitalize())
                    plt.plot(x, y, marker=marker_list.value,
                             color=PLOT_COLOR)
                    plt.tight_layout()
                    main_plot.update()
            if img:
                with main_plot:
                    plt.clf()
                    plt.imshow(data_obj[:], cmap=cmap_list.value,
                               aspect="auto")
                    plt.tight_layout()
                    main_plot.update()

    def show_data():
        """Display data getting from a hdf file"""
        file_path1 = file_path_display.text
        hdf_key1 = hdf_key_display.text
        global current_state
        if (file_path1 != "") and (hdf_key1 != "") and (hdf_key1 is not None):
            new_state = (file_path1, hdf_key1, main_slider.value,
                         hdf_value_display.text, axis_list.value,
                         cmap_list.value, display_type.value,
                         marker_list.value, min_slider.value, max_slider.value)
            if new_state != current_state:
                current_state = new_state
                try:
                    (data_type, value) = tl.get_hdf_data(file_path1, hdf_key1)
                    if (data_type == "string" or data_type == "number"
                            or data_type == "boolean"):
                        hdf_value_display.set_text(str(value))
                        with main_plot:
                            plt.clf()
                            main_plot.update()
                        reset(keep_display=True)
                    elif data_type == "array":
                        hdf_value_display.set_text("Array shape: "
                                                   "" + str(value))
                        hdf_obj = h5py.File(file_path1, "r")
                        dim = len(value)
                        if dim == 3:
                            display_3d_data(hdf_obj[hdf_key1])
                        elif dim < 3:
                            display_1d_2d_data(hdf_obj[hdf_key1],
                                               disp_type=display_type.value)
                        else:
                            ui.notify("Can't display {}-d array!".format(dim))
                            with main_plot:
                                plt.clf()
                                main_plot.update()
                            reset(keep_display=True)
                        hdf_obj.close()
                    else:
                        hdf_value_display.set_text(data_type)
                        with main_plot:
                            plt.clf()
                            main_plot.update()
                        reset(keep_display=True)
                except Exception as error:
                    reset()
                    ui.notify("Error {}".format(error))
        else:
            hdf_value_display.set_text("")
            with main_plot:
                plt.clf()
                main_plot.update()
            reset(keep_display=True)

    # =========================================================================
    #                               Build the GUI
    # =========================================================================

    # Initial parameters
    (sc_height, sc_width) = tl.get_height_width_screen()
    hei_size = RATIO * sc_width / DPI
    wid_size = RATIO * sc_height / DPI
    fig_size = (min(hei_size, MAX_FIG_SIZE[0]), min(wid_size, MAX_FIG_SIZE[1]))
    global current_state, columns, rows, image, current_slice, data_1d_2d
    current_state = None
    columns = None
    rows = None
    image = None
    current_slice = None
    data_1d_2d = None

    # For the header
    with ui.header().style("background-color: " + HEADER_COLOR).classes(
            "items-center justify-between"):
        ui.label(HEADER_TITLE).style(FONT_STYLE)

    # For the left drawer, used to display a hdf tree.
    with ui.left_drawer(fixed=True, bottom_corner=True).style(
            "background-color: " + LEFT_DRAWER_COLOR):
        with ui.row():
            tree_container = ui.column()
            with tree_container:
                async def pick_file() -> None:
                    """To pick a file when click the button 'Select file' """
                    file_path = await FilePicker("~",
                                                 allowed_extensions=INPUT_EXT)
                    if file_path:
                        file_path = file_path.replace("\\", "/")
                        file_path_display.set_text(file_path)
                        hdf_key_display.set_text("")
                        hdf_dic = tl.hdf_tree_to_dict(file_path)
                        if isinstance(hdf_dic, list):
                            tree_display = ui.card()

                            def close_file():
                                if isinstance(current_state, tuple):
                                    if file_path == current_state[0]:
                                        reset()
                                else:
                                    reset()
                                tree_container.remove(tree_display)

                            with tree_display.style("background-color: "
                                                    + TREE_BGR_COLOR):
                                ui.tree(hdf_dic, label_key="id",
                                        node_key="label", on_select=lambda e:
                                        show_key(e, file_path))
                                ui.button("Close file",
                                          on_click=lambda: close_file())
                        else:
                            ui.notify("Input must be hdf, nxs, or h5 format!")

                ui.button("Select file",
                          on_click=pick_file).props("icon=folder")

    # Layout for the main page.
    with ui.column().classes("w-full no-wrap gap-1"):
        # For displaying file-path, key, and value of a hdf/nxs/h5 file
        with ui.row().classes("w-full no-wrap"):
            with ui.row().classes("w-1/3 items-center"):
                ui.label("File path: ").style(FONT_STYLE)
                file_path_display = ui.label("")
            with ui.row().classes("w-1/3 items-center"):
                ui.label("Key: ").style(FONT_STYLE)
                hdf_key_display = ui.label("")
            with ui.row().classes("w-1/3 items-center"):
                ui.label("Value: ").style(FONT_STYLE)
                hdf_value_display = ui.label("")
        ui.separator()

        # For ui-components used to interact with 1d, 2d, or 3d data.
        with ui.row().classes("w-full justify-between items-center"):
            with ui.row().classes("items-center"):
                ui.label("Axis: ").style(FONT_STYLE)
                axis_list = ui.select(AXIS_LIST, value=AXIS_LIST[0])
            with ui.row().classes("items-center"):
                ui.label("Color map: ").style(FONT_STYLE)
                cmap_list = ui.select(CMAP_LIST, value=CMAP_LIST[0])

            async def save_image() -> None:
                """To save a slice to file when click 'Save image' """
                file_path = await FileSaver("~", title="File name (ext: .tif, "
                                                       ".jpg, .png, or .csv)")
                if file_path and image is not None:
                    file_ext = os.path.splitext(file_path)[-1]
                    if (file_ext != ".tif" and file_ext != ".jpg"
                            and file_ext != ".png" and file_ext != ".csv"):
                        ui.notify("Please use .tif, .jpg, .png, or .csv as "
                                  "file extension!")
                    else:
                        check = os.path.isfile(file_path)
                        if file_ext == ".csv":
                            error = tl.save_table(file_path, image)
                        else:
                            error = tl.save_image(file_path, image)
                        if error is not None:
                            ui.notify(error)
                        else:
                            if check:
                                ui.notify(
                                    "File {} is overwritten".format(file_path))
                            else:
                                ui.notify("File is saved at: {}".format(
                                    file_path))

            save_image_button = ui.button("Save image", on_click=save_image)

            with ui.row().classes("items-center"):
                ui.label("Display: ").style(FONT_STYLE)
                display_type = ui.select(DISPLAY_TYPE, value=DISPLAY_TYPE[0])
            with ui.row().classes("items-center"):
                ui.label("Marker: ").style(FONT_STYLE)
                marker_list = ui.select(MARKER_LIST, value=MARKER_LIST[0])

            async def save_data() -> None:
                """To save data to file when click the button 'Save data' """
                file_path = await FileSaver("~", title="File name (ext: .csv)")
                if file_path and data_1d_2d is not None:
                    file_ext = os.path.splitext(file_path)[-1]
                    if file_ext == "":
                        file_ext = ".csv"
                        file_path = file_path + file_ext
                    if file_ext != ".csv":
                        ui.notify("Please use .csv as file extension!")
                    else:
                        check = os.path.isfile(file_path)
                        error = tl.save_table(file_path, data_1d_2d)
                        if error is not None:
                            ui.notify(error)
                        else:
                            if check:
                                ui.notify(
                                    "File {} is overwritten".format(file_path))
                            else:
                                ui.notify(
                                    "File is saved at: {}".format(file_path))

            save_data_button = ui.button("Save data", on_click=save_data)

        # Slider for slicing 3d dataset
        with ui.row().classes("w-full items-center no-wrap"):
            ui.label("Slice: ").style(FONT_STYLE)
            main_slider = ui.slider(min=0, max=100, value=0).props(
                "label-always").on("update:model-value",
                                   throttle=UPDATE_RATE,
                                   leading_events=False)

        # For display data as an image, table, or plot
        main_table = ui.table(columns=columns, rows=rows, row_key="Index")
        main_plot = ui.pyplot(figsize=fig_size, close=False).classes("w-full")

        # Sliders for adjust the contrast of an image.
        with ui.row().classes("w-full justify-between no-wrap items-center"):
            ui.label("Min: ").style(FONT_STYLE)
            min_slider = ui.slider(min=0, max=254, value=0).props(
                "label-always").on("update:model-value", throttle=UPDATE_RATE,
                                   leading_events=False)

            ui.label("Max: ").style(FONT_STYLE)
            max_slider = ui.slider(min=1, max=255, value=255).props(
                "label-always").on("update:model-value", throttle=UPDATE_RATE,
                                   leading_events=False)
            ui.button("Reset", on_click=reset_min_max)

    # =========================================================================
    #                               Run the app
    # =========================================================================
    ui.timer(UPDATE_RATE, lambda: show_data())
    os.environ["NO_NETIFACES"] = "True"
    ui.run(reload=False, title="Browser-based Hdf Viewer", port=8110)


if __name__ in {"__main__", "__mp_main__"}:
    current_state = None
    columns = None
    rows = None
    image = None
    current_slice = None
    data_1d_2d = None
    main()
