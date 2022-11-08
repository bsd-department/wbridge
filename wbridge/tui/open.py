from argparse import ArgumentParser
from .subcommand import SubCommand
from ..command import powershell_command_executor
from ..misc import partition_command

class OpenSubCommand(SubCommand):
    def handle(self, args) -> int:
        # Specyfying working directory is necessary if CWD contains square brackets
        command = ["start", "-WorkingDirectory", ".", "--", args.file_or_url]
        return powershell_command_executor(*partition_command(command))

    def create_subparser(self, subparsers) -> ArgumentParser:
        """
        Add open subcommand to argument parser
        """

        open_parser = subparsers.add_parser(
            "open",
            description="Open a file or URL with the default handler on Windows.",
        )

        open_parser.add_argument(
            "file_or_url",
            help="The file or URL to be opened by Windows",
        )

        return open_parser
