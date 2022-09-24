import subprocess
import shlex
from os import makedirs, chmod
from textwrap import dedent
from pathlib import PosixPath as Path
from .misc import powershell_quote
from .pathconvert import linux_to_windows, windows_to_linux


def powershell_command_executor(command, args):
    cwd = powershell_quote(linux_to_windows(str(Path.cwd())))
    command[0] = f"Set-Location -LiteralPath {cwd}; " + command[0]
    args = list(map(powershell_quote, map(linux_to_windows, args)))

    cmd = ["powershell.exe", "-NoProfile", "-Command"] + command + args
    proc = subprocess.run(cmd)
    return proc.returncode


def linux_command_executor(command, args):
    """Executes a linux command directly."""
    proc = subprocess.run(command + list(map(windows_to_linux, args)))
    return proc.returncode


def create_command_wrapper(command):
    """
    Creates a shell script wrapper around command. Returns the path to it.
    """
    if "--" not in command:
        command.append("--")

    script = f"""\
    #!/bin/sh

    exec wb run {shlex.join(command)} "$@"
    """
    script_path = Path.home().joinpath(".local", "bin", command[0])
    makedirs(script_path.parent, exist_ok=True)

    with script_path.open("x") as f:
        f.write(dedent(script))

    chmod(script_path, 0o755)

    return script_path
