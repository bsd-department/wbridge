from sys import stderr
from argparse import REMAINDER
from .misc import add_path_conversion_options
from ..misc import partition_command, skip_leading_dashes
from ..command import powershell_command_executor, linux_command_executor


def handle_run(args):
    command_executor = powershell_command_executor
    if args.from_windows:
        command_executor = linux_command_executor

    command = skip_leading_dashes(args.command)

    if len(command) == 0:
        print("ERROR: Command cannot be empty.", file=stderr)
        return 1

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
        "command",
        nargs=REMAINDER,
        help="Command to be executed, with translated paths",
    )

    add_path_conversion_options(run_parser)
    run_parser.set_defaults(handler=handle_run)
