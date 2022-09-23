from .tui import create_argument_parser


def main():
    args = create_argument_parser().parse_args()
    return args.handler(args)
