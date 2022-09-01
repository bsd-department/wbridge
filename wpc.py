#!/usr/bin/env python3

import re
import ntpath
from os.path import realpath
from os import environ, curdir
from sys import argv, stderr

def is_url(s):
  return re.search("^[a-zA-Z]+://", s) != None

def translate_slashes(path, slash):
  return re.sub("[/\\\\]", re.escape(slash), path)

def linux_to_windows(path):
  path = path.strip()
  # Currently only used for file URLs
  protocol = ""
  slash = "\\"

  # As a special case, never touch non-file URLs
  if is_url(path):
    if not path.lower().startswith("file://"):
      return path
    protocol = "file:///"
    slash = "/"
    path = path[len("file://"):]
  # If the path isn't located in the current dir, make an absolute path instead.
  elif not realpath(path).startswith(realpath(curdir)):
    path = realpath(path)
  else:
    return translate_slashes(path, slash)

  # If the path is located on a windows drive
  drive_path = re.search("^/mnt/([a-zA-Z])(/.*)?$", path)
  if drive_path != None:
    path = "{}:{}".format(drive_path[1].upper(), drive_path[2] or '/')
    return protocol + translate_slashes(path, slash)

  # If the path is located on another WSL distro
  instance_path = re.search("^/mnt/wsl/instances/(.*)$", path)
  if instance_path != None:
    path = "//wsl$/" + instance_path[1]
    return protocol + translate_slashes(path, slash)

  # Assume the path is located on the current WSL distro
  path = "//wsl$/" + environ['WSL_DISTRO_NAME'] + path
  return protocol + translate_slashes(path, slash)

def windows_to_linux(path):
  path = path.strip()

  protocol = ""

  # Don't touch URLs
  if is_url(path):
    if not path.lower().startswith("file:///"):
      return path
    protocol = "file://"
    path = path[len("file:///"):]
  # Normalize, but also use linux slashes
  else:
    path = ntpath.normpath(path).replace("\\", "/")

  drive_path = re.search("^([a-zA-Z]):(/.*)$", path)
  if drive_path != None:
    return protocol + "/mnt/" + drive_path[1].lower() + drive_path[2]

  instance_path = re.search("^//wsl\\$/([^/]+)(/.*)?$", path)
  if instance_path != None:
    if instance_path[1] == environ['WSL_DISTRO_NAME']:
      return protocol + instance_path[2] or '/'
    return protocol + "/mnt/wsl/instances/" + instance_path[1] + (instance_path[2] or '/')

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
