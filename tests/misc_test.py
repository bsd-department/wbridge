from pathlib import PosixPath as Path
from wbridge.misc import (
    decode_octal_escapes,
    is_url,
    partition_command,
    powershell_quote,
    relative_to_subdir,
    skip_leading_dashes,
    unexpand_user,
)


def test_is_url():
    assert is_url("https://exmaple.com")
    assert not is_url("not an url")


def test_relative_to_subdir():
    assert relative_to_subdir(Path("/some/path"), "/some")
    assert not relative_to_subdir(Path("/dir"), "/dir")


def test_unexpand_user():
    assert str(unexpand_user(Path.home().joinpath("some/path"))) == "~/some/path"
    assert str(unexpand_user(Path.home())) == "~"
    assert str(unexpand_user(Path("/not/in/homedir"))) == "/not/in/homedir"


def test_decode_octal_escapes():
    assert decode_octal_escapes(r"\164\145\163\164") == "test"
    assert decode_octal_escapes("unchanged") == "unchanged"


def test_powershell_quote():
    assert powershell_quote("test'") == "'test'''"


def test_partition_command():
    assert partition_command("command arg1 arg2 arg3".split(" ")) == (
        ["command"],
        ["arg1", "arg2", "arg3"],
    )

    assert partition_command("command unprocessed -- arg1 arg2".split(" ")) == (
        ["command", "unprocessed"],
        ["arg1", "arg2"],
    )


def test_skip_leading_dashes():
    assert skip_leading_dashes("-- command arg1 arg2".split(" ")) == [
        "command",
        "arg1",
        "arg2",
    ]

    assert skip_leading_dashes("command -- arg1 arg2".split(" ")) == [
        "command",
        "--",
        "arg1",
        "arg2",
    ]
