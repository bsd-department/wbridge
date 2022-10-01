import re
from urllib.parse import urlparse
from pathlib import PosixPath as Path, PureWindowsPath
from os import environ
from .misc import is_url, relative_to_subdir
from .mounts import find_wsl_mounts


def linux_to_windows(
    input: str,
    current_distro: str | None = environ.get("WSL_DISTRO_NAME"),
) -> str:
    if current_distro is None:
        raise ValueError(
            "Distro name has to be specified manually when WSL_DISTRO_NAME is unset."
        )

    input = input.strip()

    # As a special case, never touch non-file URLs
    if is_url(input):
        scheme, _, urlpath, *_ = urlparse(input)
        if scheme != "file":
            return input
        # PureWindowsPath.as_uri() doesn't work for UNC paths.
        return "file:///" + linux_to_windows(urlpath).replace("\\", "/")

    path = Path(input)
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
        other_distro = path.parts[4]
        return str(
            PureWindowsPath("\\\\wsl$\\" + other_distro).joinpath(*path.parts[5:])
        )

    # When the path points to the current distro
    return str(PureWindowsPath("\\\\wsl$\\" + current_distro).joinpath(path))


def windows_to_linux(
    input: str,
    current_distro: str | None = environ.get("WSL_DISTRO_NAME"),
) -> str:
    if current_distro is None:
        raise ValueError(
            "Distro name has to be specified manually when WSL_DISTRO_NAME is unset."
        )

    input = input.strip()

    if is_url(input):
        scheme, _, urlpath, *_ = urlparse(input)
        if scheme != "file":
            return input
        # Skip the leading slash in URL path
        return Path(windows_to_linux(urlpath[1:])).as_uri()

    path = PureWindowsPath(input)
    if not path.is_absolute():
        return path.as_posix()

    path_prefix = None
    if (mounts := find_wsl_mounts().get(path.drive)) is not None:
        path_prefix = mounts[0]
    elif (instance_path := re.search(r"^\\\\wsl\$\\(.+)$", path.drive)) is not None:
        if instance_path[1] == current_distro:
            path_prefix = "/"
        else:
            path_prefix = "/mnt/wsl/instances/" + instance_path[1]

    if path_prefix is not None:
        return str(Path(path_prefix).joinpath(*path.parts[1:]))

    # At this point, path is probably some unmounted UNC path.
    # Since there's no clear way of converting those to WSL paths,
    # just return them instead.
    return str(path)
