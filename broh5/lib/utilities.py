"""
Module for utility methods:

    -   Get height and with of a screen.
    -   Convert hdf tree to a nested dictionary.
    -   Get data-type and value from a dataset in a hdf file.
    -   Convert 1d/2d array to a table format.
    -   Save 2d array to an image.
    -   Save 1d/2d array to a csv file.
"""

import os
import csv
import tkinter as tk
import h5py
import numpy as np
from PIL import Image


def get_height_width_screen():
    root = tk.Tk()
    screen_width = root.winfo_screenwidth()
    screen_height = root.winfo_screenheight()
    root.destroy()
    return screen_height, screen_width


def __recurse(parent_path, name, obj):
    current_path = f"{parent_path}/{name}" if parent_path else name
    if isinstance(obj, h5py._hl.dataset.Dataset):
        return [{"id": name, "label": current_path}]
    elif isinstance(obj, h5py._hl.group.Group):
        children = [__recurse(current_path, key, obj[key])
                    for key in obj.keys()]
        children = [item for sublist in children for item in sublist]
        return [{"id": name, "label": current_path, "children": children}]


def hdf_tree_to_dict(hdf_file):
    """Convert an HDF5 tree to a nested dictionary"""
    try:
        hdf_obj1 = h5py.File(hdf_file, 'r')
        result = __recurse("", "", hdf_obj1)
        file_name = os.path.basename(hdf_file)
        result[0]['id'] = file_name
        result[0]['label'] = "/"
        hdf_obj1.close()
        return result
    except Exception as error:
        return error


def get_hdf_data(file_path, dataset_path):
    """ Get data type and value from a hdf dataset """
    with h5py.File(file_path, 'r') as f:
        if dataset_path not in f:
            return "not path", None
        item = f[dataset_path]
        if isinstance(item, h5py.Group):
            return "group", None
        data_type, value = "unknown", None
        # Check the type and shape of a dataset
        if item.dtype.kind == 'S':  # Fixed-length bytes
            data = item[()]
            if item.size == 1:  # Single string or byte
                if isinstance(data, bytes):
                    data_type, value = "string", data.decode('utf-8')
                elif isinstance(data.flat[0], bytes):
                    data_type, value = "string", data.flat[0].decode('utf-8')
            else:
                data_type, value = "array", [d.decode('utf-8') for d in data]
        elif item.dtype.kind == 'U':  # Fixed-length Unicode
            data = item[()]
            if item.size == 1:  # Single string
                data_type, value = "string", data
            else:
                data_type, value = "array", list(data)
        elif h5py.check_dtype(vlen=item.dtype) in [str, bytes]:
            data = item[()]
            if isinstance(data, (str, bytes)):
                data_type, value = "string", data if isinstance(data, str) \
                    else data.decode('utf-8')
            else:
                joined_data = ''.join(
                    [d if isinstance(d, str) else d.decode('utf-8') for d in
                     data])
                data_type, value = "string", joined_data
        elif item.dtype.kind in ['i', 'f', 'u']:
            if item.shape == () or item.size == 1:
                data_type, value = "number", item[()]
            else:
                data_type, value = "array", item.shape
        elif item.dtype.kind == 'b':  # Boolean type
            data_type, value = "boolean", int(item[()])
        return data_type, value


def format_table_from_array(data):
    if len(data.shape) == 1:
        data = np.expand_dims(np.asarray(data), 1)
    (height, width) = data.shape[:2]
    if height > 1000 and width > 1000:
        rows, columns = None, None
    else:
        fm_data = np.insert(data, 0, np.arange(height), axis=1)
        columns = [{"name": "Column " + str(j), "label": "Column " + str(j),
                    "field": "Column " + str(j)} for j in range(width)]
        columns.insert(0,
                       {"name": "Index", "label": "Index", "field": "Index"})
        rows = []
        for i in range(height):
            dict_tmp = {}
            for j in range(width + 1):
                dict_tmp[columns[j]["name"]] = fm_data[i][j]
            rows.append(dict_tmp)
    return rows, columns


def save_image(file_path, mat):
    """
    Save 2D array to an image.
    """
    file_ext = os.path.splitext(file_path)[-1]
    if not ((file_ext == ".tif") or (file_ext == ".tiff")):
        mat = np.uint8(
            255.0 * (mat - np.min(mat)) / (np.max(mat) - np.min(mat)))
    image = Image.fromarray(mat)
    try:
        image.save(file_path)
    except Exception as error:
        return error


def save_table(file_path, data):
    """
    Save 1D/2D array to a csv file.
    """
    try:
        with open(file_path, 'w', newline='') as file:
            if len(data.shape) == 1:
                data = np.expand_dims(np.asarray(data), 1)
            writer = csv.writer(file)
            writer.writerows(data)
    except Exception as error:
        return error
