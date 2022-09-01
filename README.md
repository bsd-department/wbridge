# WSL Path Converter

A simple command line tool which can convert Linux WSL paths/file URLs to
windows paths/file URLS or vice versa.

## Features
- Supports non-existing paths, unlike built-in `wslpath`.
- Supports file URLs
- Supports paths to other WSL distros[^1]

[^1]: Only works after following [this guide](https://askubuntu.com/a/1395784).

## Usage
The first argument to `wpc.py` is the type of paths to be converted. Can be
either `windows` or `linux`. The rest are either path or file urls to be
converted. Non-path and non-file URLs will be printed without changes(unless
they contain trailing or leading whitespace).
