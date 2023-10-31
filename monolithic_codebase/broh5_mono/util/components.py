"""
Module for GUI components:

    -   Dialog for selecting a file.
    -   Dialog for saving a file.
"""

import os
import string
import platform
from pathlib import Path
from typing import Optional, List
from nicegui import ui
from nicegui.events import GenericEventArguments


class FilePicker(ui.dialog):

    def __init__(self, directory: str, *,
                 upper_limit: Optional[str] = None,
                 show_hidden_files: bool = False,
                 allowed_extensions: Optional[List[str]] = None) -> None:
        """
        This is a simple file picker that allows users to select a file from
        the local filesystem where the app is running.
        Codes are adapted from an example of NiceGUI:
        https://github.com/zauberzeug/nicegui/tree/main/examples/local_file_picker

        Parameters
        ----------

        directory : str
            Starting directory.
        upper_limit : str
            Stopping directory (None: no limit).
        show_hidden_files : bool
            Whether to show hidden files.
        allowed_extensions : list of str
            Only show files with given extension. E.g. ['hdf', 'h5', 'nxs']

        Returns
        -------
            file path.
        """
        super().__init__()
        self.show_hidden_files = show_hidden_files
        self.allowed_extensions = allowed_extensions
        self.drives_toggle = None
        self.path = Path(directory).expanduser()
        if upper_limit is None:
            self.upper_limit = None
        else:
            self.upper_limit = Path(
                directory if upper_limit is ... else upper_limit).expanduser()
        with self, ui.card():
            self.add_drives_toggle()
            self.grid = ui.aggrid(
                {'columnDefs': [{'field': 'name', 'headerName': 'File'}],
                 'rowSelection': 'single'}, html_columns=[0]).classes(
                'w-96').on('cellDoubleClicked', self.handle_double_click)
            with ui.row().classes('w-full justify-end'):
                ui.button('Cancel', on_click=self.close).props('outline')
                ui.button('Ok', on_click=self.handle_ok)
        self.update_grid()

    def check_extension(self, filename: str) -> bool:
        """Check if the filename has an allowed extension."""
        if self.allowed_extensions is None:
            return True
        else:
            return filename.split('.')[-1].lower() in self.allowed_extensions

    def add_drives_toggle(self):
        """Give a list of available drivers in a WinOS computer"""
        if platform.system() == 'Windows':
            drives = ['%s:\\' % d for d in string.ascii_uppercase if
                      os.path.exists('%s:' % d)]
            self.path = Path(drives[0]).expanduser()
            self.drives_toggle = ui.toggle(drives, value=drives[0],
                                           on_change=self.__update_drive)

    def __update_drive(self):
        if self.drives_toggle:
            self.path = Path(self.drives_toggle.value).expanduser()
            self.update_grid()

    def update_grid(self) -> None:
        paths = list(self.path.glob('*'))
        if not self.show_hidden_files:
            paths = [p for p in paths if not p.name.startswith('.')]
        if self.allowed_extensions:
            paths = [p for p in paths if
                     p.is_dir() or self.check_extension(p.name)]
        paths.sort(key=lambda p: p.name.lower())
        paths.sort(key=lambda p: not p.is_dir())

        self.grid.options['rowData'] = [
            {'name': f'📁 <strong>{p.name}</strong>' if p.is_dir() else p.name,
             'path': str(p), } for p in paths]
        if (self.upper_limit is None
                and self.path != self.path.parent
                or self.upper_limit is not None
                and self.path != self.upper_limit):
            self.grid.options['rowData'].insert(0, {
                'name': '📁 <strong>..</strong>',
                'path': str(self.path.parent), })
        self.grid.update()

    def handle_double_click(self, e: GenericEventArguments) -> None:
        self.path = Path(e.args['data']['path'])
        if self.path.is_dir():
            self.update_grid()
        else:
            self.submit(str(self.path))

    async def handle_ok(self):
        rows = await ui.run_javascript(
            f'getElement({self.grid.id}).gridOptions.api.getSelectedRows()')
        fpath = [r['path'] for r in rows]
        self.submit(fpath[0])


class FileSaver(ui.dialog):

    def __init__(self, directory: str, *, upper_limit: Optional[str] = None,
                 show_hidden_files: bool = False,
                 title: Optional[str] = 'File name') -> None:
        """
        This is a simple file saver dialog that allows users to specify a
        file name and where the file should be saved.

        Parameters
        ----------

        directory : str
            Starting directory.
        upper_limit : str
            Stopping directory (None: no limit).
        show_hidden_files : bool
            Whether to show hidden files.

        Returns
        -------
            file path.
        """
        super().__init__()
        self.show_hidden_files = show_hidden_files
        self.drives_toggle = None
        self.path = Path(directory).expanduser()
        self.title = title
        if upper_limit is None:
            self.upper_limit = None
        else:
            self.upper_limit = Path(
                directory if upper_limit is ... else upper_limit).expanduser()

        with self, ui.card():
            self.add_drives_toggle()
            self.grid = ui.aggrid(
                {'columnDefs': [{'field': 'name', 'headerName': 'File'}],
                 'rowSelection': 'single'}, html_columns=[0]).classes(
                'w-96').on('cellDoubleClicked', self.handle_double_click)
            # Input field for filename
            self.filename_input = ui.input(self.title).classes(
                'w-full justify-between').on('keydown.enter',
                                             self.handle_save)
            with ui.row().classes('w-full justify-between'):
                ui.button('Create Folder',
                          on_click=self.create_folder_dialog).props('outline')
                ui.button('Cancel', on_click=self.close).props('outline')
                ui.button('Save', on_click=self.handle_save)
        self.update_grid()

    def add_drives_toggle(self):
        """Give a list of available drivers in a WinOS computer"""
        if platform.system() == 'Windows':
            drives = ['%s:\\' % d for d in string.ascii_uppercase if
                      os.path.exists('%s:' % d)]
            self.path = Path(drives[0]).expanduser()
            self.drives_toggle = ui.toggle(drives, value=drives[0],
                                           on_change=self.__update_drive)

    def __update_drive(self):
        if self.drives_toggle:
            self.path = Path(self.drives_toggle.value).expanduser()
            self.update_grid()

    def update_grid(self) -> None:
        paths = list(self.path.glob('*'))
        if not self.show_hidden_files:
            paths = [p for p in paths if not p.name.startswith('.')]
        paths.sort(key=lambda p: p.name.lower())
        paths.sort(key=lambda p: not p.is_dir())

        self.grid.options['rowData'] = [
            {'name': f'📁 <strong>{p.name}</strong>' if p.is_dir() else p.name,
             'path': str(p)} for p in paths]
        if (self.upper_limit is None
                and self.path != self.path.parent
                or self.upper_limit is not None
                and self.path != self.upper_limit):
            self.grid.options['rowData'].insert(0, {
                'name': '📁 <strong>..</strong>',
                'path': str(self.path.parent)})
        self.grid.update()

    def handle_double_click(self, e: GenericEventArguments) -> None:
        self.path = Path(e.args['data']['path'])
        if self.path.is_dir():
            self.update_grid()
        else:
            self.filename_input.value = self.path.name
            self.path = self.path.parent

    def handle_save(self):
        filename = self.filename_input.value
        if not filename:
            ui.notify('File name cannot be empty!')
            return
        save_path = self.path / filename
        save_path_str = str(save_path).replace('\\', '/')
        self.submit(save_path_str)

    async def create_folder_dialog(self):
        """Open a dialog to get the name of the new folder and create it."""
        with ui.dialog().classes('w-100 h-100') as dialog, ui.card():
            with ui.column():
                folder_name_input = ui.input('Folder Name').classes(
                    'w-full justify-between')
                with ui.row():
                    ui.button('Cancel', on_click=dialog.close).props('outline')
                    ui.button('Create', on_click=lambda: self.create_folder(
                        folder_name_input.value, dialog))
        await dialog

    def create_folder(self, folder_name: str, dialog: ui.dialog):
        if not folder_name:
            ui.notify('Folder name cannot be empty!')
            return
        new_folder_path = self.path / folder_name
        if new_folder_path.exists():
            ui.notify(f"A folder named '{folder_name}' already exists!")
            return
        new_folder_path.mkdir(parents=True, exist_ok=True)
        self.update_grid()
        dialog.close()
