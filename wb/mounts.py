from collections import namedtuple
from functools import cache
from .misc import decode_octal_escapes


MountedDevice = namedtuple("MountedDevice", ["device", "mount", "fstype"])


def parse_mounts():
    """
    Returns a list of MountedDevice objects, representing each device/mount pair.
    """
    with open("/proc/mounts") as f:
        return [
            MountedDevice._make(map(decode_octal_escapes, line.strip().split(" ")[:3]))
            for line in f
        ]


@cache
def find_wsl_mounts():
    """
    Returns a dict of drives/UNC shares mapped to lists of their WSL mount points
    """
    ret = {}
    for device, mount, fstype in parse_mounts():
        # WSL mount detection could also be done based on mount options
        # But this is currently enough
        if fstype != "9p" or "\\" not in device:
            continue

        # Store drives like PureWindowsPath.drive for easy lookup
        ret.setdefault(device.rstrip, []).append(mount)

    return ret
