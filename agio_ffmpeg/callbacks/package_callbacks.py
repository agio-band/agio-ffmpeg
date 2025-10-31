from agio.core.workspaces import AWorkspaceManager, APackageManager
from agio_ffmpeg.lib import binary_helper


def on_installed(package: APackageManager, ws_manager: AWorkspaceManager):
    # TODO use cache
    if not ws_manager.bin_path.exists():
        raise FileExistsError('Binary dir not exists. Workspace not installed?')
    # download ffmpeg binary
    print('Download ffmpeg to', ws_manager.bin_path)
    binary_helper.download_binary(ws_manager.bin_path.as_posix())


def after_uninstalling(package: APackageManager, ws_manager: AWorkspaceManager):
    # delete ffmpeg binary
    bin_path = ws_manager.bin_path.as_posix()
    binary_helper.cleanup_binary(bin_path)


