from abc import ABC, abstractmethod
from argparse import ArgumentParser

class SubCommand(ABC):
    def __init__(self, subparsers):
        parser = self.create_subparser(subparsers)
        parser.set_defaults(handler=self.handle)

    @staticmethod
    def _add_path_conversion_options(parser: ArgumentParser):
        """
        Adds --from-windows and --from-linux options to parser.
        """
        conversion_group = parser.add_mutually_exclusive_group()
        conversion_group.add_argument(
            "-l", "--from-linux",
            action="store_true",
            help="Convert linux paths to windows paths. This is done by default",
        )  # fmt: skip

        conversion_group.add_argument(
            "-w", "--from-windows",
            action="store_true",
            help="Convert windows paths to linux paths",
        )  # fmt: skip

    @abstractmethod
    def handle(self, args) -> int:
        pass

    @abstractmethod
    def create_subparser(self, subparsers) -> ArgumentParser:
        pass
