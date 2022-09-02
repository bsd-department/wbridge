#!/usr/bin/env python3

import re
from pathlib import Path, PureWindowsPath
from urllib.parse import urlparse
from os.path import relpath
from os import environ
from sys import argv, stderr

def is_url(s):
  return re.search("^[a-zA-Z]+://", s) != None

def relative_to_subdir(path, d):
  """
  Returns true if path is relative to some subdir of d
  """
  subdir_index = len(Path(d).parts)
  return path.is_relative_to(d) and len(path.parts) > subdir_index

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
  rel_path = relpath(path)

  if is_rel and not rel_path.startswith(".."):
    return rel_path.replace("/", "\\")

  # If the path is located on a windows drive
  # /mnt/<drive letter>/rest/of/path
  if relative_to_subdir(path, "/mnt") and len(path.parts[2]) == 1:
    drive_letter = path.parts[2].upper()
    # When path leads to the drive root directory
    return str(PureWindowsPath(drive_letter + ":\\").joinpath(*path.parts[3:]))

  # When the path points to another wsl distro
  # /mnt/wsl/instances/<distro name>/path
  if relative_to_subdir(path, "/mnt/wsl/instances"):
    distro_name = path.parts[4]
    return str(PureWindowsPath("\\\\wsl$\\" + distro_name).joinpath(*path.parts[5:]))

  # When the path points to the current distro
  return str(PureWindowsPath("\\\\wsl$\\" + environ['WSL_DISTRO_NAME']).joinpath(path))

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

  drive_path = re.search("^([a-zA-Z]):$", path.drive)
  if drive_path != None:
    return str(Path("/mnt/" + drive_path[1].lower()).joinpath(*path.parts[1:]))

  instance_path = re.search("^\\\\\\\\wsl\\$\\\\(.+)$", path.drive)
  if instance_path != None:
    if instance_path[1] == environ['WSL_DISTRO_NAME']:
      return str(Path("/").joinpath(*path.parts[1:]))
    return str(Path("/mnt/wsl/instances/" + instance_path[1]).joinpath(*path.parts[1:]))

  # At this point, path is probably some non-WSL UNC path.
  # Since there's no clear way of converting those to WSL paths,
  # just return them instead.
  return str(path)

def help(name):
  print(f"USAGE: {name} <windows|linux> [windows/linux paths]...", file=stderr)

def main(args):
  if len(args) <= 2:
    help(args[0])
    return 1
  path_type = args[1]
  path_converter = None
  if path_type == "windows":
    path_converter = windows_to_linux
  elif path_type == "linux":
    path_converter = linux_to_windows
  else:
    help(args[0])
    return 1

  for p in map(path_converter, args[2:]):
    print(p)

  return 0

if __name__ == '__main__':
  exit(main(argv))
