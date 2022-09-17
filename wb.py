#!/usr/bin/env python3

import re
import subprocess
from pathlib import Path, PureWindowsPath
from urllib.parse import urlparse
from os import environ, chmod, makedirs
from sys import stderr
from argparse import ArgumentParser, REMAINDER
from textwrap import dedent


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

    if is_rel and path.is_relative_to(Path.cwd()):
        return str(path.relative_to(Path.cwd())).replace("/", "\\")

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


def partition_command(args):
    """
    Splits the command line into the command and argument parts.
    """
    command, args = [args[0]], args[1:]
    if "--" in args:
        command_end_marker = args.index("--")
        command += args[0:command_end_marker]
        args = args[command_end_marker + 1:]
    return command, list(args)


def powershell_quote(argument):
    return "'{}'".format(argument.replace("'", "''"))


def powershell_command_executor(command, args):
    cwd = powershell_quote(linux_to_windows(str(Path.cwd())))
    command[0] = f"Set-Location -LiteralPath {cwd}; " + command[0]
    command = ["powershell.exe", "-NoProfile", "-Command"] + command
    args = list(map(powershell_quote, map(linux_to_windows, args)))
    proc = subprocess.run(command + args)
    return proc.returncode


def linux_command_executor(command, args):
    """Executes a linux command directly."""
    proc = subprocess.run(command + list(map(windows_to_linux, args)))
    return proc.returncode


def save_command(command, args):
    full_command = command + ["--"] + args
    script = f'''\
    #!/bin/sh

    exec {Path(__file__).resolve()} run {" ".join(full_command)} "$@"
    '''
    script_path = Path.home().joinpath("bin", command[0])
    makedirs(script_path.parent, exist_ok=True)

    with script_path.open('w') as f:
        f.write(dedent(script))

    chmod(script_path, 0o755)

    print(f"Command successfully saved in '{script_path}'")
    if str(script_path.parent) not in environ["PATH"].split(":"):
        print(dedent('''\
        WARNING: It appears ~/bin is not currently in $PATH
                 Consider adding this line somewhere to your .bashrc or .profile:
                 export PATH=~/bin:"$PATH"
        '''), end='')


def handle_run(args):
    command_executor = powershell_command_executor
    if args.from_windows:
        command_executor = linux_command_executor

    command = args.command
    if len(command) == 0:
        print("ERROR: Command cannot be empty.", file=stderr)
        return 1

    if command[0] == "--":
        # Because of argparse.REMAINDER usage, leading -- has to be removed
        # manually. Non leading -- serves as a unprocessed argument separator,
        # so it's fine.
        command = command[1:]

    if args.save:
        save_command(*partition_command(command))
        return 0

    return command_executor(*partition_command(command))


def handle_open(args):
    if args.from_windows:
        print("ERROR: This command can only be used from linux.",
              file=stderr)
        return 1

    # Specyfying working directory is necessary if CWD contains square brackets
    command = ["start", "-WorkingDirectory", ".", "--", args.file_or_url]
    return powershell_command_executor(*partition_command(command))


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
    parser = ArgumentParser(exit_on_error=False, description="""
    WBridge - enhanced WSL/Windows interop
    """)

    conversion_group = parser.add_mutually_exclusive_group()
    conversion_group.add_argument("-l", "--from-linux",
                                  action="store_true",
                                  help="Convert linux paths to windows paths. This is done by default")
    conversion_group.add_argument("-w", "--from-windows",
                                  action="store_true",
                                  help="Convert windows paths to linux paths")

    subparsers = parser.add_subparsers(required=True)

    run_parser = subparsers.add_parser("run", description="""
    Execute a command with command line arguments converted.
    If '--' was passed as an argument, then only arguments after it are
    converted. If you wish to pass '--' directly to the command, pass it twice.
    """)
    run_parser.add_argument('-s', '--save',
                            action="store_true",
                            help="Instead of running, save the command as a shell script in ~/bin")
    run_parser.add_argument("command",
                            nargs=REMAINDER,
                            help='Command to be executed, with translated paths')
    run_parser.set_defaults(handler=handle_run)

    open_parser = subparsers.add_parser("open", description="""
    Open a file or URL with the default handler on Windows.
    """)
    open_parser.add_argument("file_or_url",
                             help='The file or URL to be opened by Windows')
    open_parser.set_defaults(handler=handle_open)

    convert_parser = subparsers.add_parser("convert", description="""
    Convert one or more paths.
    """)
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
