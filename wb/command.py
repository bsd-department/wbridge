import subprocess
from pathlib import PosixPath as Path
from .misc import powershell_quote, partition_command
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
