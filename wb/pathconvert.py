import re
from urllib.parse import urlparse
from pathlib import PosixPath as Path, PureWindowsPath
from os import environ
from .misc import is_url, relative_to_subdir
from .mounts import find_wsl_mounts


def linux_to_windows(path):
    path = path.strip()

    # As a special case, never touch non-file URLs
    if is_url(path):
        scheme, _, urlpath, *_ = urlparse(path)
        if scheme != "file":
            return path
        # PureWindowsPath.as_uri() doesn't work for UNC paths.
        return "file:///" + linux_to_windows(urlpath).replace("\\", "/")

    path = Path(path)
    is_rel = not path.is_absolute()

    path = path.resolve()

    if is_rel and path.is_relative_to(Path.cwd()):
        return str(path.relative_to(Path.cwd())).replace("/", "\\")

    # If the path is located on a windows drive or a mounted UNC share
    for windows_root, mountpoints in find_wsl_mounts().items():
        for mount in mountpoints:
            if path.is_relative_to(mount):
                return str(
                    PureWindowsPath(windows_root + "\\").joinpath(
                        path.relative_to(mount)
                    )
                )

    # When the path points to another wsl distro
    # /mnt/wsl/instances/<distro name>/path
    if relative_to_subdir(path, "/mnt/wsl/instances"):
        distro_name = path.parts[4]
        return str(
            PureWindowsPath("\\\\wsl$\\" + distro_name).joinpath(*path.parts[5:])
        )

    # When the path points to the current distro
    return str(
        PureWindowsPath("\\\\wsl$\\" + environ["WSL_DISTRO_NAME"]).joinpath(path)
    )


def windows_to_linux(path):
    path = path.strip()

    if is_url(path):
        scheme, _, urlpath, *_ = urlparse(path)
        if scheme != "file":
            return path
        # Skip the leading slash in URL path
        return Path(windows_to_linux(urlpath[1:])).as_uri()

    path = PureWindowsPath(path)
    if not path.is_absolute():
        return path.as_posix()

    path_prefix = None
    if (mounts := find_wsl_mounts().get(path.drive)) is not None:
        path_prefix = mounts[0]
    elif (
        instance_path := re.search("^\\\\\\\\wsl\\$\\\\(.+)$", path.drive)
    ) is not None:
        if instance_path[1] == environ["WSL_DISTRO_NAME"]:
            path_prefix = "/"
        else:
            path_prefix = "/mnt/wsl/instances/" + instance_path[1]

    if path_prefix is not None:
        return str(Path(path_prefix).joinpath(*path.parts[1:]))

    # At this point, path is probably some unmounted UNC path.
    # Since there's no clear way of converting those to WSL paths,
    # just return them instead.
    return str(path)
