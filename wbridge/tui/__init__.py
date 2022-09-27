from argparse import ArgumentParser
from .convert import implement_convert
from .open import implement_open
from .run import implement_run
from .screenshot import implement_screenshot
from .alias import implement_alias


def create_argument_parser() -> ArgumentParser:
    parser = ArgumentParser(
        description="WBridge - enhanced WSL/Windows interop",
    )

    subparsers = parser.add_subparsers(required=True)

    # fmt: off
    for impl in [implement_run,
                 implement_alias,
                 implement_open,
                 implement_screenshot,
                 implement_convert]:
        impl(subparsers)
    # fmt: on

    return parser


def main() -> int:
    args = create_argument_parser().parse_args()
    return args.handler(args)
