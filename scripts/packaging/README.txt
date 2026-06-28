HORTICALC PORTABLE APP
======================

Start
-----
Windows: double-click Horticalc.exe.
Linux: run ./horticalc.

Horticalc starts a private local service on 127.0.0.1 and opens the interface
in an Edge, Chrome, or Chromium app window. It does not expose the service to
the local network.

Keep the extracted folder writable. Do not run the app from Program Files or
directly inside the archive.

Your data
---------
Shipped defaults live in data/ and recipes/. Your edits and new profiles are
stored as overrides in user/. Back up user/ to preserve your work.

To reset Horticalc, close the app and rename user/ to user-backup/. The next
launch creates a fresh user folder. Restoring user-backup/ restores your saved
work.

Troubleshooting
---------------
Runtime logs are stored in logs/launcher.log. Include the relevant log excerpt
when reporting a startup problem.

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
