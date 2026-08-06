# Quickstart

Status: `operation-guide`.

## Packaged Release

1. Download the latest release archive for your platform.
2. Extract the archive to a writable folder.
3. Run the executable:
   - Windows: `Horticalc.exe`
   - Linux: `./horticalc`

The launcher starts a local server on `127.0.0.1`, waits for the health check,
and opens the GUI in a native Horticalc window. Windows 10/11 requires the
[Microsoft WebView2 Runtime](https://developer.microsoft.com/microsoft-edge/webview2/).
The Linux x86_64 release requires the system GTK 3/WebKitGTK 4.1 runtime:

```bash
# Ubuntu 22.04/24.04, Debian 13, or Linux Mint 22.3
sudo apt update && sudo apt install -y libgirepository-1.0-1 gir1.2-webkit2-4.1

# Fedora 44
sudo dnf install -y webkit2gtk4.1
```

Ubuntu 22.04/24.04, Debian 13, and Fedora 44 are tested automatically. Linux
Mint 22.3 has a required manual VM gate. Other Linux distributions are best
effort and must provide compatible GTK 3 and WebKitGTK 4.1 system packages.
Horticalc never invokes `sudo` or installs packages itself. Windows 7, 8, and
8.1 are not supported.
Source installs support Python 3.10 through 3.13; packaged releases carry their
own Python runtime.

## Source Install

The fastest path from source is in [commands.md](commands.md#install-and-run-from-source).

## First 30 Seconds

1. Open the GUI. The default view is the **Calculator**.
2. In the **Configuration** card, set the batch volume and display units.
3. In the **Fertilizer components** table, select a fertilizer and enter a dose.
4. Click **Calculate**. The live sidebar and result tables update with the solution output.
5. Switch to the **Solver** to enter a target profile and let the solver choose doses.

For more detail, see the [user guide](user_guide.md) and the command reference in [commands.md](commands.md).
