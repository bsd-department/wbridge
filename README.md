# WSL Path Converter

A simple command line tool which can convert Linux WSL paths/file URLs to
windows paths/file URLS or vice versa.

## Features
- Supports non-existing paths, unlike built-in `wslpath`.
- Supports file URLs
- Supports paths to other WSL distros[^1]
- Supports execution of programs with automatic command line path conversions.

[^1]: Only works after following [this guide](https://askubuntu.com/a/1395784).

## Requirements
- Python 3.8+
- WSL2

## Usage

There are 2 modes of operation: path conversion of a single or multiple paths or
command execution with conversion of paths in command line arguments, which
works kind of like `sudo`.

### Examples

Convert linux paths to windows paths:

``` sh
wpc.py convert /etc/passwd /mnt/c/Users/User/Desktop/file.txt /mnt/wsl/instances/distro/etc/hosts
# Output:
# \\wsl$\<current distro name>\etc\passwd
# C:\Users\User\Desktop\file.txt
# \\wsl$\distro\etc\hosts
```

Convert windows paths to linux paths:

``` sh
wpc.py -w convert C:\Windows \\wsl$\<current-distro>\etc\sudoers D:/some/path
# Output:
# /mnt/c/Windows
# /etc/sudoers
# /mnt/d/some/path
```

Run windows programs, with command line paths translated:

``` sh
wpc.py run mpv /mnt/d/file.mp4
# Equivalent to:
powershell.exe -NoProfile -Command mpv 'D:\file.mp4'
```
