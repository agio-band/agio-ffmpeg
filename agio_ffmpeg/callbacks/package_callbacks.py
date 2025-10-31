import itertools
import logging
import os
import shutil
import stat
import tarfile
import tempfile
from pathlib import Path

from agio.core.workspaces import AWorkspaceManager, APackageManager
from agio.tools import network as net

WINDOWS_URL = 'https://github.com/BtbN/FFmpeg-Builds/releases/download/latest/ffmpeg-master-latest-win64-gpl-shared.zip'
LINUX_URL = 'https://github.com/BtbN/FFmpeg-Builds/releases/download/latest/ffmpeg-master-latest-linux64-gpl.tar.xz'
MACOS_URL = (
    'https://evermeet.cx/ffmpeg/ffmpeg-8.0.zip',
    'https://evermeet.cx/ffmpeg/ffprobe-8.0.zip'
)
EXT = '.exe.' if os.name == 'nt' else ''
TOOLS_TO_INSTALL = ['ffmpeg'+EXT, 'ffprobe'+EXT]
logger = logging.getLogger(__name__)


def on_installed(package: APackageManager, ws_manager: AWorkspaceManager):
    # TODO use cache
    if not ws_manager.bin_path.exists():
        raise FileExistsError('Binary dir not exists. Workspace not installed?')
    # download ffmpeg binary
    print('Download ffmpeg to', ws_manager.bin_path)
    files = download_binary(ws_manager.bin_path.as_posix())
    if os.name != 'nt':
        for file in files:
            file = Path(file)
            mode = file.stat().st_mode
            file.chmod(mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)


def after_uninstalling(package: APackageManager, ws_manager: AWorkspaceManager):
    # delete ffmpeg binary
    print('Uninstalling ffmpeg package')
    cleanup_binary(ws_manager.bin_path.as_posix())


# tools

def get_link_list():
    if os.name == 'nt':
        return (WINDOWS_URL,)
    elif os.name == 'posix':
        return (LINUX_URL,)
    elif os.name == 'darwin':
        return MACOS_URL
    else:
        raise ValueError('Unknown OS')


def extract_tools(src_directory, destination_dir):
    result = []
    for tool_name in TOOLS_TO_INSTALL:
        for path in src_directory.rglob(tool_name):
            if path.is_file():
                logger.info(f'Copy file: {path.name}')
                dest = Path(destination_dir) / path.name
                shutil.copyfile(path, dest)
                result.append(dest)
    return result


def download_binary(destination_dir: str|Path):
    # delete old
    cleanup_binary(destination_dir)
    # download latest versions
    links = get_link_list()
    copied_files = []
    with tempfile.TemporaryDirectory() as tmpdir:
        download_dir = Path(tmpdir, 'downloaded')
        for link in links:
            logger.info(f'Download file: {link}')
            net.download_file(link, download_dir.as_posix(), allow_redirects=True)
        extract_dir = Path(tmpdir, 'extracted')
        # extract tar
        for archive in itertools.chain(Path(download_dir).rglob('*.tar*')):
            logger.info(f'Extracting archive: {archive}')
            with tarfile.open(archive, "r:xz") as tar:
                tar.extractall(path=extract_dir/archive.name)
            files = extract_tools(extract_dir/archive.name, destination_dir)
            copied_files.extend(files)
        # extract zip
        for archive in Path(tmpdir).rglob('*.zip'):
            logger.info(f'Extracting archive: {archive}')
            shutil.unpack_archive(archive, extract_dir/archive.name)
            files = extract_tools(extract_dir / archive.name, destination_dir)
            copied_files.extend(files)
    return copied_files


def cleanup_binary(source_dir):
    for tool in TOOLS_TO_INSTALL:
        for path in Path(source_dir).rglob(tool):
            path.unlink()

