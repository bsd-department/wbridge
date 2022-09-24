from argparse import REMAINDER
from os import environ
from pathlib import PosixPath as Path
from sys import stderr
from textwrap import dedent
from ..command import create_command_wrapper
from ..misc import skip_leading_dashes, unexpand_user


def handle_save(args):
    command = skip_leading_dashes(args.command)
    if len(command) == 0:
        print("ERROR: Command cannot be empty.", file=stderr)
        return 1

    try:
        script_path = create_command_wrapper(command, args.binpath.expanduser())
    except FileExistsError as e:
        print(f"ERROR: File '{e.filename}' already exists.", file=stderr)
        return 1

    print(f"Command successfully saved in '{script_path}'")

    if str(script_path.parent) not in environ["PATH"].split(":"):
        unexpanded = unexpand_user(script_path.parent)
        msg = f"""\
        WARNING: It appears {unexpanded} is not currently in $PATH
                 Consider adding this line somewhere to your .bashrc or .profile:
                 export PATH="{unexpanded}${{PATH:+":$PATH"}}"
        """
        print(dedent(msg), end="", file=stderr)

    return 0


def implement_save(parser):
    """
    Add save subcommand to argument parser
    """
    save_parser = parser.add_parser(
        "save",
        description="""
        Save a command as a shell script to be executed with WBridge
        """,
    )

    save_parser.add_argument(
        "-b", "--binpath",
        help="Directory where the script will be saved. By default: ~/.local/bin",
        default=Path.home().joinpath(".local", "bin"),
        type=Path
    )  # fmt: skip

    save_parser.add_argument(
        "command", nargs=REMAINDER, help="Command to be saved in the shell script."
    )

    save_parser.set_defaults(handler=handle_save)
