import re
from pathlib import PosixPath as Path


def is_url(s):
    return re.search("^[a-zA-Z]+://", s) is not None


def relative_to_subdir(path, directory):
    """
    Returns true if path is relative to some subdir of directory
    """
    subdir_index = len(Path(directory).parts)
    return path.is_relative_to(directory) and len(path.parts) > subdir_index


def decode_octal_escapes(s):
    """
    Replaces all octal escapes with their corresponding character
    """
    return re.sub("\\\\([0-7]{3})", lambda m: chr(int(m[1], 8)), s)


def powershell_quote(s):
    return "'{}'".format(s.replace("'", "''"))


def partition_command(args):
    """
    Splits the command line into the command and argument parts.
    """
    command, args = [args[0]], args[1:]
    if "--" in args:
        command_end_marker = args.index("--")
        command += args[0:command_end_marker]
        args = args[command_end_marker + 1 :]
    return command, list(args)
