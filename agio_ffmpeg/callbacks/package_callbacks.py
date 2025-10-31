from agio.tools import app_dirs
from agio_ffmpeg.lib import binary_helper


def on_installed(package):
    # download ffmpeg binary
    binary_helper.download_binary(app_dirs.binary_files_dir())


def after_uninstalling(package):
    # delete ffmpeg binary
    binary_helper.cleanup_binary(app_dirs.binary_files_dir())


