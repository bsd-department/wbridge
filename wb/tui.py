import shlex
from pathlib import PosixPath as Path
from os import makedirs, chmod, environ
from sys import stderr
from textwrap import dedent
from datetime import datetime
from argparse import ArgumentParser, REMAINDER
from .command import powershell_command_executor, linux_command_executor
from .pathconvert import linux_to_windows, windows_to_linux
from .misc import partition_command
from .screenshot import save_screenshot


def save_command(command):
    if "--" not in command:
        command.append("--")

    script = f"""\
    #!/bin/sh

    exec wb run {shlex.join(command)} "$@"
    """
    script_path = Path.home().joinpath("bin", command[0])
    makedirs(script_path.parent, exist_ok=True)

    with script_path.open("w") as f:
        f.write(dedent(script))

    chmod(script_path, 0o755)

    print(f"Command successfully saved in '{script_path}'")
    if str(script_path.parent) not in environ["PATH"].split(":"):
        msg = """\
        WARNING: It appears ~/bin is not currently in $PATH
                 Consider adding this line somewhere to your .bashrc or .profile:
                 export PATH=~/bin:"$PATH"
        """
        print(dedent(msg), end="")


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
        if args.from_windows:
            msg = """\
            ERROR: Saving the command and passing --from-windows isn't supported yet.
            """
            print(dedent(msg), file=stderr, end="")
            return 1
        save_command(command)
        return 0

    return command_executor(*partition_command(command))


def handle_open(args):
    # Specyfying working directory is necessary if CWD contains square brackets
    command = ["start", "-WorkingDirectory", ".", "--", args.file_or_url]
    return powershell_command_executor(*partition_command(command))


def handle_screenshot(args):
    if args.raw:
        if args.pattern is None:
            print("ERROR: File name is required in raw mode.", file=stderr)
            return 1
        output_name = args.pattern
    else:
        pattern = args.pattern or "%Y-%m-%d %H.%M.%S.png"

        output_name = datetime.now().strftime(pattern)

    output_file = str(Path(output_name).resolve())

    save_screenshot(output_file)
    return 0


def handle_convert(args):
    path_mapper = linux_to_windows
    line_ender = "\n"
    if args.from_windows:
        path_mapper = windows_to_linux

    if args.null:
        line_ender = "\0"

    for p in map(path_mapper, args.paths):
        print(p, end=line_ender)

    return 0


def add_path_conversion_options(parser):
    """
    Adds --from-windows and --from-linux options to parser.
    """
    conversion_group = parser.add_mutually_exclusive_group()
    conversion_group.add_argument(
        "-l", "--from-linux",
        action="store_true",
        help="Convert linux paths to windows paths. This is done by default",
    )  # fmt: skip

    conversion_group.add_argument(
        "-w", "--from-windows",
        action="store_true",
        help="Convert windows paths to linux paths",
    )  # fmt: skip


def create_argparser():
    parser = ArgumentParser(
        description="WBridge - enhanced WSL/Windows interop",
    )

    subparsers = parser.add_subparsers(required=True)

    run_parser = subparsers.add_parser(
        "run",
        description="""
        Execute a command with command line arguments converted.
        If '--' was passed as an argument, then only arguments after it are
        converted. If you wish to pass '--' directly to the command,
        pass it twice.
        """,
    )

    run_parser.add_argument(
        "-s", "--save",
        action="store_true",
        help="Instead of running, save the command as a shell script in ~/bin",
    )  # fmt: skip

    run_parser.add_argument(
        "command",
        nargs=REMAINDER,
        help="Command to be executed, with translated paths",
    )

    add_path_conversion_options(run_parser)
    run_parser.set_defaults(handler=handle_run)

    open_parser = subparsers.add_parser(
        "open",
        description="Open a file or URL with the default handler on Windows.",
    )

    open_parser.add_argument(
        "file_or_url",
        help="The file or URL to be opened by Windows",
    )

    open_parser.set_defaults(handler=handle_open)

    screenshot_parser = subparsers.add_parser(
        "screenshot",
        description="Take a screenshot and save it in the current directory.",
    )

    screenshot_parser.add_argument(
        "pattern",
        nargs="?",
        help="Output file name. Can contain strftime format codes.",
    )

    screenshot_parser.add_argument(
        "-r", "--raw",
        action="store_true",
        help="Interpret file argument literally, without strftime",
    )  # fmt: skip

    screenshot_parser.set_defaults(handler=handle_screenshot)

    convert_parser = subparsers.add_parser(
        "convert",
        description="Convert one or more paths.",
    )

    convert_parser.add_argument(
        "-0", "--null",
        action="store_true",
        help="Separate paths with the null character instead of newline",
    )  # fmt: skip

    convert_parser.add_argument(
        "paths",
        nargs="+",
        help="Paths to be converted.",
    )

    add_path_conversion_options(convert_parser)
    convert_parser.set_defaults(handler=handle_convert)

    return parser
