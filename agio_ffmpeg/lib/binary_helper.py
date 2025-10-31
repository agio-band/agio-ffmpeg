import os
import tarfile
import tempfile
from pathlib import Path
from agio.tools import network as net
import shutil
import itertools
import logging


WINDOWS_URL = 'https://github.com/BtbN/FFmpeg-Builds/releases/download/latest/ffmpeg-master-latest-win64-gpl-shared.zip'
LINUX_URL = 'https://github.com/BtbN/FFmpeg-Builds/releases/download/latest/ffmpeg-master-latest-linux64-gpl.tar.xz'
MACOS_URL = (
    'https://evermeet.cx/ffmpeg/ffmpeg-8.0.zip',
    'https://evermeet.cx/ffmpeg/ffprobe-8.0.zip'
)
EXT = '.exe.' if os.name == 'nt' else ''
TOOLS_TO_INSTALL = ['ffmpeg'+EXT, 'ffprobe'+EXT]
logger = logging.getLogger(__name__)


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
    for tool_name in TOOLS_TO_INSTALL:
        for path in src_directory.rglob(tool_name):
            if path.is_file():
                logger.info(f'Copy file: {path.name}')
                shutil.copyfile(path, Path(destination_dir) / path.name)


def download_binary(destination_dir: str|Path):
    # delete old
    cleanup_binary(destination_dir)
    # download latest versions
    links = get_link_list()
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
            extract_tools(extract_dir/archive.name, destination_dir)
        # extract zip
        for archive in Path(tmpdir).rglob('*.zip'):
            logger.info(f'Extracting archive: {archive}')
            shutil.unpack_archive(archive, extract_dir/archive.name)
            extract_tools(extract_dir / archive.name, destination_dir)


def cleanup_binary(source_dir):
    for tool in TOOLS_TO_INSTALL:
        for path in Path(source_dir).rglob(tool):
            path.unlink()

