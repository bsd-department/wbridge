from .misc import add_path_conversion_options
from ..command import linux_to_windows, windows_to_linux


def handle_convert(args) -> int:
    path_mapper = linux_to_windows
    line_ender = "\n"
    if args.from_windows:
        path_mapper = windows_to_linux

    if args.null:
        line_ender = "\0"

    for p in map(path_mapper, args.paths):
        print(p, end=line_ender)

    return 0


def implement_convert(subparsers):
    """
    Adds convert subcommand to argument parser
    """
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
