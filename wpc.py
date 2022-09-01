#!/usr/bin/env python3

import re
import ntpath
from os.path import realpath
from os import environ, curdir
from sys import argv, stderr

def is_url(s):
  return re.search("^[a-zA-Z]+://", s) != None

def linux_to_windows(path):
  path = path.strip()

  # As a special case, never touch URLs
  if is_url(path):
    return path

  winpath = None
  # If relative, only replace slashes
  if realpath(path).startswith(realpath(curdir)):
    winpath = path
  else:
    winpath = realpath(path)

  # Convert all linux slashes to windows slashes
  winpath = re.sub("/+", "\\\\", winpath)
  # Replace duplicated backslashes with just one
  winpath = re.sub("\\\\+", "\\\\", winpath)

  # True if not absolute
  if not winpath.startswith("\\"):
    return winpath

  # If the path is located on a windows drive
  drive_path = re.search("^\\\\mnt\\\\([a-zA-Z])(\\\\.*)?$", winpath)
  if drive_path != None:
    return "{}:{}".format(drive_path[1].upper(), drive_path[2] or '\\')

  # If the path is located on another WSL distro
  instance_path = re.search("^\\\\mnt\\\\wsl\\\\instances\\\\(.*)$", winpath)
  if instance_path != None:
    return "\\\\wsl$\\" + instance_path[1]

  # Assume the path is located on the current WSL distro
  return "\\\\wsl$\\" + environ['WSL_DISTRO_NAME'] + winpath

def windows_to_linux(path):
  path = path.strip()

  # Don't touch URLs
  if is_url(path):
    return path

  # Normalize, but also use linux slashes
  path = ntpath.normpath(path).replace("\\", "/")

  drive_path = re.search("^([a-zA-Z]):(/.*)$", path)
  if drive_path != None:
    return "/mnt/" + drive_path[1].lower() + drive_path[2]

  instance_path = re.search("^//wsl\\$/([^/]+)(/.*)?$", path)
  if instance_path != None:
    if instance_path[1] == environ['WSL_DISTRO_NAME']:
      return instance_path[2] or '/'
    return "/mnt/wsl/instances/" + instance_path[1] + (instance_path[2] or '/')

  # Assume path is relative
  return path

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
