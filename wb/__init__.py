from .tui import create_argparser


def main():
    args = create_argparser().parse_args()
    return args.handler(args)
