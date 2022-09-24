from os import environ
from sys import stderr
from textwrap import dedent
from argparse import REMAINDER
from .misc import add_path_conversion_options
from ..misc import partition_command, unexpand_user
from ..command import (
    powershell_command_executor,
    linux_command_executor,
    create_command_wrapper,
)


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

        try:
            script_path = create_command_wrapper(command)
        except FileExistsError as e:
            print(f"ERROR: File '{e.filename}' already exists.")
            return 1

        print(f"Command successfully saved in '{script_path}'")

        if str(script_path.parent) not in environ["PATH"].split(":"):
            unexpanded = unexpand_user(script_path.parent)
            msg = f"""\
            WARNING: It appears {unexpanded} is not currently in $PATH
                     Consider adding this line somewhere to your .bashrc or .profile:
                     export PATH="{unexpanded}${{PATH:+":$PATH"}}"
            """
            print(dedent(msg), end="")

        return 0

    return command_executor(*partition_command(command))


def implement_run(parser):
    """
    Add run subcommand to argument parser
    """
    run_parser = parser.add_parser(
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
