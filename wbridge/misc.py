import re
from pathlib import PosixPath as Path


def is_url(s: str) -> bool:
    return re.search("^[a-zA-Z]+://", s) is not None


def relative_to_subdir(path: Path, directory: str) -> bool:
    """
    Returns true if path is relative to some subdir of directory
    """
    subdir_index = len(Path(directory).parts)
    return path.is_relative_to(directory) and len(path.parts) > subdir_index


def unexpand_user(path: Path) -> Path:
    """
    Returns path, with home directory replaced with ~
    """
    if path.is_relative_to(Path.home()):
        return Path("~").joinpath(path.relative_to(Path.home()))
    return path


def decode_octal_escapes(s: str) -> str:
    """
    Replaces all octal escapes with their corresponding character
    """
    return re.sub(r"\\([0-7]{3})", lambda m: chr(int(m[1], 8)), s)


def powershell_quote(s: str) -> str:
    return "'{}'".format(s.replace("'", "''"))


def partition_command(args: list[str]) -> tuple[list[str], list[str]]:
    """
    Splits the command line into the command and argument parts.
    """
    command, args = [args[0]], args[1:]
    if "--" in args:
        command_end_marker = args.index("--")
        command += args[0:command_end_marker]
        args = args[command_end_marker + 1 :]
    return command, args


def skip_leading_dashes(command: list[str]) -> list[str]:
    """
    Returns command, but with leading -- skipped.
    It is necessary because argparse.REMAINDER doesn't do this automatically.
    """
    if len(command) >= 1 and command[0] == "--":
        return command[1:]
    return command
