#!/usr/bin/env python3

import re
import subprocess
from pathlib import Path, PureWindowsPath
from urllib.parse import urlparse
from os.path import relpath, basename
from os import environ
from sys import argv, stderr
from argparse import ArgumentParser, REMAINDER


def is_url(s):
    return re.search("^[a-zA-Z]+://", s) is not None


def relative_to_subdir(path, directory):
    """
    Returns true if path is relative to some subdir of directory
    """
    subdir_index = len(Path(directory).parts)
    return path.is_relative_to(directory) and len(path.parts) > subdir_index


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

    if is_rel and not (rel_path := relpath(path)).startswith(".."):
        return rel_path.replace("/", "\\")

    # If the path is located on a windows drive
    # /mnt/<drive letter>/rest/of/path
    if relative_to_subdir(path, "/mnt") and len(path.parts[2]) == 1:
        drive_letter = path.parts[2].upper()
        # When path leads to the drive root directory
        return str(PureWindowsPath(drive_letter + ":\\")
                   .joinpath(*path.parts[3:]))

    # When the path points to another wsl distro
    # /mnt/wsl/instances/<distro name>/path
    if relative_to_subdir(path, "/mnt/wsl/instances"):
        distro_name = path.parts[4]
        return str(PureWindowsPath("\\\\wsl$\\" + distro_name)
                   .joinpath(*path.parts[5:]))

    # When the path points to the current distro
    return str(PureWindowsPath("\\\\wsl$\\" + environ['WSL_DISTRO_NAME'])
               .joinpath(path))


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
    if (drive_path := re.search("^([a-zA-Z]):$", path.drive)) is not None:
        path_prefix = "/mnt/" + drive_path[1].lower()
    elif (instance_path := re.search("^\\\\\\\\wsl\\$\\\\(.+)$",
                                     path.drive)) is not None:
        if instance_path[1] == environ['WSL_DISTRO_NAME']:
            path_prefix = "/"
        else:
            path_prefix = "/mnt/wsl/instances/" + instance_path[1]

    if path_prefix is not None:
        return str(Path(path_prefix).joinpath(*path.parts[1:]))

    # At this point, path is probably some non-WSL UNC path.
    # Since there's no clear way of converting those to WSL paths,
    # just return them instead.
    return str(path)


def partition_command(*args):
    unprocessed_args, args = [args[0]], args[1:]
    if "--" in args:
        unprocessed_marker = args.index("--")
        unprocessed_args += args[0:unprocessed_marker]
        args = args[unprocessed_marker + 1:]
    return unprocessed_args, list(args)


def execute_command(*args, command_mapper=None, path_mapper=linux_to_windows):
    unprocessed_args, args = partition_command(*args)
    if command_mapper is not None:
        unprocessed_args, args = command_mapper(unprocessed_args, args)
    proc = subprocess.run(unprocessed_args + list(map(path_mapper, args)))
    return proc.returncode


def run_with_cmd(unprocessed_args, args):
    """
    Makes sure the command is run through cmd.exe.
    Some windows programs require a windows shell for command line output.
    """
    return ["cmd.exe", "/c"] + unprocessed_args, args


def handle_run(args):
    command_mapper = run_with_cmd
    path_mapper = linux_to_windows
    if args.from_windows:
        command_mapper = None
        path_mapper = windows_to_linux

    command = args.command
    if len(command) == 0:
        print("ERROR: Command cannot be empty.", file=stderr)
        return 1

    if command[0] == "--":
        # Because of argparse.REMAINDER usage, leading -- has to be removed
        # manually. Non leading -- serves as a unprocessed argument separator,
        # so it's fine.
        command = command[1:]

    return execute_command(*command,
                           command_mapper=command_mapper,
                           path_mapper=path_mapper)


def handle_convert(args):
    path_mapper = linux_to_windows
    line_ender = '\n'
    if args.from_windows:
        path_mapper = windows_to_linux

    if args.null:
        line_ender = '\0'

    for p in map(path_mapper, args.paths):
        print(p, end=line_ender)

    return 0


def create_argparser():
    parser = ArgumentParser(exit_on_error=False)

    conversion_group = parser.add_mutually_exclusive_group()
    conversion_group.add_argument("-l", "--from-linux",
                                  action="store_true",
                                  help="Convert linux paths to windows paths. This is done by default")
    conversion_group.add_argument("-w", "--from-windows",
                                  action="store_true",
                                  help="Convert windows paths to linux paths")

    subparsers = parser.add_subparsers(required=True)

    run_parser = subparsers.add_parser("run")
    run_parser.add_argument("command",
                            nargs=REMAINDER,
                            help='Command to be executed, with translated paths')
    run_parser.set_defaults(handler=handle_run)

    convert_parser = subparsers.add_parser("convert")
    convert_parser.add_argument("-0", "--null",
                                action='store_true',
                                help='Separate paths with the null character instead of newline')
    convert_parser.add_argument("paths",
                                nargs='+',
                                help='Paths to be converted.')
    convert_parser.set_defaults(handler=handle_convert)

    return parser


if __name__ == '__main__':
    args = create_argparser().parse_args()
    exit(args.handler(args))
