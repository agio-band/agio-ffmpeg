import hashlib
import json
import logging
import os
import shutil
import stat
import tarfile
import tempfile
from pathlib import Path

from agio.core.workspaces import AWorkspaceManager, APackageManager
from agio.tools import network as net
from agio.tools.cache_tools import get_files_from_cache, save_file_to_cache

WINDOWS_DATA = [
    {
        'url':'https://github.com/BtbN/FFmpeg-Builds/releases/download/latest/ffmpeg-master-latest-win64-gpl-shared.zip',
        'files': [
            ('bin/ffmpeg.exe', 'ffmpeg.exe'),
            ('bin/ffprobe.exe', 'ffprobe.exe'),
        ]
     }
]
LINUX_DATA = [
    {
        'url':'https://github.com/BtbN/FFmpeg-Builds/releases/download/latest/ffmpeg-master-latest-linux64-gpl.tar.xz',
        'files': [
            ('bin/ffmpeg', 'ffmpeg'),
            ('bin/ffprobe', 'ffprobe'),
        ]
    }
]
MACOS_DATA = [
    {
        'url': 'https://evermeet.cx/ffmpeg/ffmpeg-8.0.zip',
        'files': [
            ('ffmpeg', 'ffmpeg'),
        ]
    },
    {
        'url': 'https://evermeet.cx/ffmpeg/ffprobe-8.0.zip',
        'files': [
            ('ffprobe', 'ffprobe'),
        ]
    }
]


logger = logging.getLogger(__name__)


def on_installed(package: APackageManager, ws_manager: AWorkspaceManager):
    # TODO use cache
    if not ws_manager.bin_path.exists():
        raise FileExistsError('Binary dir not exists. Workspace not installed?')
    # download ffmpeg binary
    logger.info('Download ffmpeg to %s', ws_manager.bin_path)
    info = get_info_data()
    files = get_remote_files(info, ws_manager.bin_path.as_posix())
    if os.name != 'nt':
        for file in files:
            file = Path(file)
            mode = file.stat().st_mode
            file.chmod(mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)


def after_uninstalling(package: APackageManager, ws_manager: AWorkspaceManager):
    # delete ffmpeg binary
    logger.info('Uninstalling ffmpeg binary')
    cleanup_binary(ws_manager.bin_path.as_posix())


# tools

def get_info_data():
    if os.name == 'nt':
        return WINDOWS_DATA
    elif os.name == 'posix':
        return LINUX_DATA
    elif os.name == 'darwin':
        return MACOS_DATA
    else:
        raise ValueError('Unknown OS')


def cleanup_binary(source_dir):
    info = get_info_data()
    for inf in info:
        for _, path in inf['files']:
            full_path = Path(source_dir, path)
            if full_path.exists():
                full_path.unlink()


def get_remote_files(remote_info_list: list[dict], target_dir: str) -> list:
    result_files = []
    key = hashlib.sha1(json.dumps(remote_info_list, sort_keys=True).encode('utf-8')).hexdigest()  # type: ignore
    try:
        result_files = list(get_files_from_cache(key))
    except FileNotFoundError:
        for inf in remote_info_list:
            for root, rel_path in download_remove_files(inf):
                for archive_file, save_path in inf['files']:
                    if str(rel_path) == archive_file:
                        full_path, relative = save_file_to_cache(key, root / rel_path, save_path)
                        result_files.append((full_path, relative))
    for full_path, rel_path in result_files:
        link_path = Path(target_dir, rel_path)
        link_path.parent.mkdir(parents=True, exist_ok=True)
        if link_path.exists():
            link_path.unlink()
        link_path.hardlink_to(full_path)
        logger.info(f'Linked file: {rel_path}')
    return [x[0] for x in result_files]


def download_remove_files(remote_info: dict) -> list:
    with tempfile.TemporaryDirectory() as tmpdir:
        download_dir = Path(tmpdir, 'downloaded')
        logger.info(f'Download file: {remote_info["url"]}')
        net.download_file(remote_info["url"], download_dir.as_posix(), allow_redirects=True, skip_exists=True)
        extract_dir = Path(tmpdir, 'extracted')
        archive = next(Path(download_dir).iterdir(), None)
        if not archive:
            raise FileNotFoundError('No archive found, Download failed.')
        if archive.stat().st_size == 0:
            raise FileNotFoundError('Downloaded file is empty, Download failed.')
        archive_dir = extract_archive(archive, extract_dir)
        for file in archive_dir.rglob('*'):
            if file.is_file():
                yield archive_dir, file.relative_to(archive_dir)


def extract_archive(archive_path: Path, target_path: Path):
    logger.info(f'Extracting archive: {archive_path}')
    if archive_path.name.endswith('tar') or archive_path.name.endswith('tar.xz'):
        with tarfile.open(archive_path, "r:xz") as tar:
            tar.extractall(path=target_path.as_posix())
    elif archive_path.suffix == '.zip':
        shutil.unpack_archive(archive_path, target_path)
    else:
        raise ValueError(f'Unsupported archive type: {archive_path}')
    return next(target_path.iterdir())


