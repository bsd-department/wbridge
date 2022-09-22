# WBridge

WBridge is a command line utility designed to enhance the experience of interacting
with Windows from WSL.

## Features
- Seamlessly run windows applications from WSL, with Linux paths translated into
  Windows paths.
- Supports opening files and URLs using the default application set under Windows.
- Supports path conversion of non-existing paths and file URLs, unlike built-in `wslpath`.
- Supports paths to other WSL distros[^1]
- Supports arbitrary mount points of windows drives and UNC shares

[^1]: Only works after following [this guide](https://askubuntu.com/a/1395784).

## Requirements
- Python 3.8+
- WSL2

## Examples

Run windows programs, with command line paths translated:

``` sh
wb.py run mpv /mnt/d/file.mp4
# Equivalent to:
powershell.exe -NoProfile -Command mpv 'D:\file.mp4'
```

Save a command as a shell script in ~/bin to run it directly

``` sh
wb.py run --save mpv
mpv some/file.mp4
# Equivalent to
wb.py run mpv -- some/file.mp4
```

Open a file or URL using the default Windows application:

``` sh
wb.py open image.jpg
wb.py open https://example.com
```

Convert linux paths to windows paths:

``` sh
wb.py convert /etc/passwd /mnt/c/Users/User/Desktop/file.txt /mnt/wsl/instances/distro/etc/hosts
# Output:
# \\wsl$\<current distro name>\etc\passwd
# C:\Users\User\Desktop\file.txt
# \\wsl$\distro\etc\hosts
```

Convert windows paths to linux paths:

``` sh
wb.py convert -w C:\Windows \\wsl$\<current-distro>\etc\sudoers D:/some/path
# Output:
# /mnt/c/Windows
# /etc/sudoers
# /mnt/d/some/path
```
