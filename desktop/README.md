# Zapcart Board on your taskbar

Puts the Control Board on your Desktop, Start Menu and taskbar with the Zapcart
logo, opening in its own window with no address bar — it looks and behaves like
a desktop application, not a browser tab.

## Install

1. Keep all three files in the same folder:
   - `Install Zapcart Board.cmd`
   - `Install-ZapcartBoard.ps1`
   - `ZapcartBoard.ico`
2. Double-click **`Install Zapcart Board.cmd`**.
3. When it finishes, open the board from the Desktop icon, then right-click its
   taskbar button and choose **Pin to taskbar**.

Windows 11 does not let a script pin to the taskbar, so that last right-click is
yours. Everything else is automatic.

## What it does

- Copies the logo to `%LOCALAPPDATA%\Zapcart`
- Finds Edge, Chrome or Brave and builds a shortcut that opens the board with
  `--app=`, which is what removes the browser chrome
- Falls back to your default browser if none of those are installed
- Adds the shortcut to the Desktop and the Start Menu

Nothing is installed system-wide and nothing runs in the background. To remove
it, delete the shortcuts and the `%LOCALAPPDATA%\Zapcart` folder.

If `ZapcartBoard.ico` is missing the installer still works — you just get the
browser's icon instead of the Zapcart logo. Put the file back and run it again.

## The board

https://claude.ai/artifact/BzDjpcTEGnMWXwPZfpLxG4

It updates itself as the hourly dispatcher works, so leave it open. **Do** marks
an item finished, **Later** hides it and brings it back. Both are saved to the
board's own database, so they hold across your phone, your PC and every refresh.

On iPhone, open that address in Safari and use Share → **Add to Home Screen** for
the same thing on the phone.
