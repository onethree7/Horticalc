HORTICALC PORTABLE APP
======================

Start
-----
Windows: double-click Horticalc.exe.
Linux: run ./horticalc.

The recommended Windows release is horticalc-<version>-windows-setup.exe. It
installs for the current user under %LocalAppData%\Programs\Horticalc without
administrator rights. The setup and executable are not Authenticode-signed;
verify the official release checksum before accepting an Unknown publisher
warning. Setup updates and uninstall both preserve user/, while uninstall
removes logs/. The ZIP remains the fully supported portable alternative.

Windows portable ZIP: before extracting, right-click the downloaded ZIP, open
Properties, select Unblock/Zulassen, and click Apply. Then extract the complete
archive to a writable folder. If it was already extracted while blocked,
back up an existing user/ folder, delete the extracted folder, and repeat these
steps with the original ZIP.

Horticalc starts a private local service on 127.0.0.1 and opens the interface
in its own native desktop window. It does not require or control an installed
browser, and it does not expose the service to the local network.

Windows 10/11 requires the Microsoft WebView2 Runtime. The Linux x86_64 build
requires the system GTK 3 and WebKitGTK 4.1 runtime. Install it before starting:

Ubuntu, Debian, Linux Mint:
sudo apt update && sudo apt install -y libgirepository-1.0-1 gir1.2-webkit2-4.1

Fedora:
sudo dnf install -y webkit2gtk4.1

Automated release tests cover Ubuntu 22.04/24.04, Debian 13, and Fedora 44.
Linux Mint 22.3 is a required manual VM test. Windows 7, 8, and 8.1 are not
supported.

Keep the extracted folder writable. Do not run the app from Program Files or
directly inside the archive.

Your data
---------
Shipped defaults live in data/ and recipes/. Shipped calculator recipes are
zero-water reference calculations, not crop feed recommendations. Your edits
and new profiles are stored as overrides in user/. Back up user/ to preserve
your work.

To reset Horticalc, close the app and rename user/ to user-backup/. The next
launch creates a fresh user folder. Restoring user-backup/ restores your saved
work.

Troubleshooting
---------------
Runtime logs are stored in logs/launcher.log. Include the relevant log excerpt
when reporting a startup problem.

On Windows, Horticalc checks whether Mark of the Web blocks the bundled
Python.Runtime.dll. If it reports this condition, back up an existing user/
folder first, delete the extracted folder, unblock the original ZIP as described
above, and extract it again. Horticalc does not remove Windows security metadata
automatically.

Project documentation and issue tracker:
https://github.com/onethree7/Horticalc

Product data and manufacturer schedules
---------------------------------------
Horticalc is an independent project. It is not affiliated with, sponsored,
endorsed, or approved by any manufacturer, brand owner, retailer, publisher,
water utility, or other data source named in the application. Product names
and trademarks are used only to identify the referenced products and remain
the property of their respective owners.

Bundled fertilizer data, product compositions, recipes, and manufacturer
schedules are point-in-time snapshots of information available when they were
recorded. They may be incomplete, inaccurate, or out of date and are provided
without warranty. Before every use, obtain and check the manufacturer's current
official product label, safety data sheet, technical data sheet, and current
application or feed schedule. Those official documents always take precedence.
Do not use Horticalc's bundled data or calculated output as the sole source for
mixing, dosing, compatibility, or safety decisions.

License and source
------------------
Copyright (C) 2026 Horticalc contributors.

Horticalc is free software under the GNU General Public License, version 3 or
(at your option) any later version. It comes without any warranty. The full
license is included in LICENSE.

The corresponding source code and release build scripts are available at:
https://github.com/onethree7/Horticalc

For a release archive, use the source from the matching version tag or commit.
