import logging
import os
import stat
from pathlib import Path
import platform

from agio.core.workspaces import AWorkspaceManager, APackageManager
from agio.tools import network as net

FILE_NAME = f'ffmpeg-{platform.system().lower()}.zip'


logger = logging.getLogger(__name__)


def on_installed(package: APackageManager, ws_manager: AWorkspaceManager):
    ws_manager.bin_path.mkdir(parents=True, exist_ok=True)
    # download ffmpeg binary
    dep_dir = Path(net.download_dependency(FILE_NAME))
    if not dep_dir:
        raise FileNotFoundError('No dependency found, Download failed.')
    # create hardlinks
    target_dir = ws_manager.bin_path
    created_files = []
    for file in Path(dep_dir).iterdir():
        target_file = Path(target_dir, file.name)
        target_file.hardlink_to(file)
        created_files.append(target_file)
    if os.name != 'nt':
        for file in created_files:
            mode = file.stat().st_mode
            file.chmod(mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)


# def after_uninstalling(package: APackageManager, ws_manager: AWorkspaceManager):
    # delete ffmpeg binary
    # logger.info('Uninstalling ffmpeg binary')
    # cleanup_binary(ws_manager.bin_path.as_posix())


