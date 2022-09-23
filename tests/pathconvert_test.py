from wbridge.pathconvert import linux_to_windows as l2w, windows_to_linux as w2l
from wbridge.mounts import find_wsl_mounts
from os import environ
from unittest.mock import patch


def path_conversion_ensure_equivalent(linux_path, windows_path, *, absolute=True):
    """
    Makes sure both paths are equivalent when converting.
    """
    windows_path_forward_slash = windows_path.replace("\\", "/")

    assert l2w(linux_path) == windows_path
    assert w2l(windows_path) == w2l(windows_path_forward_slash) == linux_path

    # file URLs are always absolute
    if absolute:
        windows_file_url = "file:///" + windows_path_forward_slash
        linux_file_url = "file://" + linux_path
        assert w2l(windows_file_url) == linux_file_url
        assert l2w(linux_file_url) == windows_file_url


def test_drive_path_conversion():
    path_conversion_ensure_equivalent("/mnt/c/Windows", "C:\\Windows")


def test_other_distro_path_conversion():
    path_conversion_ensure_equivalent(
        "/mnt/wsl/instances/distro/etc/shadow", "\\\\wsl$\\distro\\etc\\shadow"
    )


def test_current_distro_path_conversion():
    if environ.get("WSL_DISTO_NAME") is None:
        environ["WSL_DISTRO_NAME"] = "Ubuntu-22.04"
    distro = environ["WSL_DISTRO_NAME"]
    path_conversion_ensure_equivalent("/etc/hosts", f"\\\\wsl$\\{distro}\\etc\\hosts")


def test_relative_path_conversion():
    path_conversion_ensure_equivalent("a/b/c/d", "a\\b\\c\\d", absolute=False)
    path_conversion_ensure_equivalent("--help", "--help", absolute=False)


@patch.dict(find_wsl_mounts(), {"C:": ["/mnt/c", "/completely/arbitrary"]}, clear=True)
def test_arbitrary_mount_path_conversion():
    assert (
        l2w("/mnt/c/Windows") == l2w("/completely/arbitrary/Windows") == "C:\\Windows"
    )
