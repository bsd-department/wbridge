from argparse import REMAINDER, ArgumentParser
from os import environ
from pathlib import PosixPath as Path
from sys import stderr
from textwrap import dedent
from .subcommand import SubCommand
from ..command import create_command_wrapper
from ..misc import skip_leading_dashes, unexpand_user


class AliasSubCommand(SubCommand):
    def handle(self, args) -> int:
        command = skip_leading_dashes(args.command)
        if len(command) == 0:
            print("ERROR: Command cannot be empty.", file=stderr)
            return 1

        try:
            script_path = create_command_wrapper(
                command,
                binary_path=args.binpath.expanduser(),
                wrapper_name=args.with_name,
            )
        except FileExistsError as e:
            print(f"ERROR: File '{e.filename}' already exists.", file=stderr)
            return 1

        print(f"Command successfully saved in '{script_path}'")

        if str(script_path.parent) not in environ["PATH"].split(":"):
            unexpanded = unexpand_user(script_path.parent)
            msg = f"""\
            WARNING: It appears {unexpanded} is not currently in $PATH
                     Consider adding this line somewhere to your .bashrc or .profile:
                     export PATH={unexpanded}"${{PATH:+":$PATH"}}"
            """
            print(dedent(msg), end="", file=stderr)
        return 0

    def create_subparser(self, subparsers) -> ArgumentParser:
        """
        Add alias subcommand to argument parser
        """
        alias_parser: ArgumentParser = subparsers.add_parser(
            "alias",
            description="""\
            Create a shell script that runs specified command through WBridge
            """,
        )

        alias_parser.add_argument(
            "-b", "--binpath",
            help="Directory where the script will be saved. Default: ~/.local/bin",
            default=Path.home().joinpath(".local", "bin"),
            type=Path
        )  # fmt: skip

        alias_parser.add_argument(
            "--with-name",
            help="""\
            Specify the file name for the script. If not specified,
            command name will be used as the script name.
            """,
        )

        alias_parser.add_argument(
            "command",
            nargs=REMAINDER,
            help="Command to be saved in the shell script."
        )

        return alias_parser
