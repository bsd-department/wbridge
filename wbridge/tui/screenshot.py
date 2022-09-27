from argparse import _SubParsersAction as SubParsers, ArgumentParser
from sys import stderr
from datetime import datetime
from pathlib import PosixPath as Path
from ..screenshot import save_screenshot


def handle_screenshot(args) -> int:
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


def implement_screenshot(subparsers: SubParsers[ArgumentParser]):
    """
    Adds screenshot subcommand to argument parser
    """
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
