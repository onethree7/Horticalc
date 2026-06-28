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
