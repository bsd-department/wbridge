from argparse import ArgumentParser
from .alias import AliasSubCommand
from .convert import ConvertSubCommand
from .open import OpenSubCommand
from .run import RunSubCommand
from .screenshot import ScreenshotSubCommand


def create_argument_parser() -> ArgumentParser:
    parser = ArgumentParser(
        description="WBridge - enhanced WSL/Windows interop",
    )

    subparsers = parser.add_subparsers(required=True)

    for c in [
            AliasSubCommand,
            ConvertSubCommand,
            OpenSubCommand,
            RunSubCommand,
            ScreenshotSubCommand,
    ]:
        c(subparsers)

    return parser


def main() -> int:
    args = create_argument_parser().parse_args()
    return args.handler(args)
