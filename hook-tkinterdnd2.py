"""PyInstaller hook that includes tkinterdnd2's native TkDnD libraries."""

from PyInstaller.utils.hooks import collect_data_files

datas = collect_data_files("tkinterdnd2")
