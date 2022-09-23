import subprocess
from textwrap import dedent
from tempfile import NamedTemporaryFile
from .pathconvert import linux_to_windows


def save_screenshot(path):
    """
    Saves screenshot in path. Path should be absolute and a string
    """

    script = """\
    Add-Type -AssemblyName System.Windows.Forms
    Add-Type -AssemblyName System.Drawing

    function screenshot($path) {
        $bounds = [System.Windows.Forms.Screen]::PrimaryScreen.Bounds
        $bmp = New-Object Drawing.Bitmap $bounds.Width, $bounds.Height
        $graphics = [Drawing.Graphics]::FromImage($bmp)

        $null = $graphics.CopyFromScreen($bounds.Location,
                                         [Drawing.Point]::Empty,
                                         $bounds.Size)

        $bmp.Save($path)

        $graphics.Dispose()
        $bmp.Dispose()
    }
    screenshot $($args[0])
    """

    with NamedTemporaryFile("w", suffix=".ps1") as f:
        f.write(dedent(script))
        f.flush()

        # fmt: off
        cmd = ["powershell.exe",
               "-NoProfile",
               "-ExecutionPolicy", "Bypass",
               "-File"] + list(map(linux_to_windows, [f.name, path]))
        # fmt: on
        subprocess.run(cmd).check_returncode()
