from pathlib import Path
import os
from agio.core.workspaces import AWorkspaceManager
from agio.tools import paths

SUFFIX = '.exe' if os.name == 'nt' else ''


def get_ffmpeg_tool(name="ffmpeg"):
    binary = get_ffmpeg_binary_dir().joinpath(name).with_suffix(SUFFIX)
    if not binary.exists():
        raise FileNotFoundError(f'ffmpeg tool not found "{name}"')
    return paths.expand_windows_path(binary)


def get_ffmpeg_binary_dir() -> Path:
    manager = AWorkspaceManager.current()
    if not manager:
        raise RuntimeError('No current workspace defined')
    return manager.bin_path
