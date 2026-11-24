# 3MF context-menu sanitizer

[Instrucciones en español](README.es.md)

This optional, independent tool corrects `raft_first_layer_expansion` and
`tree_support_wall_count` when their value is `-1`. It does not need a slicer
and does not replace the existing folder-monitoring application.

Normally it creates a **new file** alongside the original. For example,
`model.3mf` becomes `model_sanitizado.3mf`. The original is unchanged, and an
existing output is never overwritten. If neither setting needs correcting,
no new file is created.

## Windows 10 and 11

The included executable is for 64-bit Windows. Python and administrator rights
are not required.

### Installation

1. Open [Sanitizador3MF.exe](windows/prebuilt/Sanitizador3MF.exe) and use
   GitHub's **Download raw file** button to download it.
2. Open the downloaded file. Windows may display a security warning for an
   unsigned executable; check that it came from the expected repository before
   deciding whether to run it.
3. When asked whether to add **Sanitizar 3MF** to the right-click menu, select
   **Sí** (Yes). Wait for the confirmation.
4. The application installs a per-user copy under
   `%LOCALAPPDATA%\Programs\Sanitizador3MF`. You do not need to start the
   downloaded installer each time.

### Usage

1. Open File Explorer and find the `.3mf` you want to fix.
2. Right-click the file. On Windows 10, choose **Sanitizar 3MF**. On Windows 11,
   choose **Show more options** first, then **Sanitizar 3MF**; the option may
   appear directly if the classic context menu is already enabled.
3. Read the result message. If corrections were needed, open the new
   `_sanitizado.3mf` file in your slicer.

![Windows right-click menu](screenshots/windows-context-menu.jpg)
![Example result message](screenshots/windows-result.jpg)

An error is displayed if the file is invalid or the output already exists. If
the file already exists, rename or move the existing output before trying again.
Selecting multiple files processes each separately.

### Uninstall

Open Windows **Settings > Apps**, select **Sanitizador 3MF**, and uninstall it.
Alternatively, open the installer again and choose the uninstall option. If the
installed executable is running during removal, the message gives its path so
you can delete it after closing the window.

## Ubuntu with Files (Nautilus)

The tool requires Python 3.10 or later and the Nautilus file manager. Installation
is for the current user; it does not require `sudo`. For desktop result messages,
`notify-send` or `zenity` must be available.

### Download and install

1. On the repository page, select the branch containing this change. Choose
   **Code > Download ZIP**, then extract the ZIP in Files. Alternatively, while
   this pull request is pending, clone its branch:

   ```sh
   git clone --branch feature/context-menu-sanitizer https://github.com/mvisions/3mf-Sanitizer.git
   ```

2. Open a terminal in the extracted or cloned repository folder. Install the
   tool:

   ```sh
   cd context-menu/linux
   bash install.sh
   ```

3. Without `python3-nautilus`, the option appears under **Scripts**. To display
   it directly in the context menu instead, install the package, rerun the
   installer and restart Files:

   ```sh
   sudo apt install python3-nautilus
   bash install.sh
   nautilus -q
   ```

   The last two commands assume the terminal is still in `context-menu/linux`.
   Restarting Nautilus closes its open Files windows; reopen Files afterward.
   The package installation may request your system password.

### Usage

1. In Files, right-click a local `.3mf` file.
2. Select **Sanitizar 3MF**, or **Scripts > Sanitizar 3MF** if the direct
   extension is not installed. The direct menu also supports selecting several
   local 3MF files.
3. Check the desktop notification and open the new `_sanitizado.3mf` file in
   your slicer. If no changes are needed, no copy is created.

If the option is missing, verify that Files is Nautilus and rerun the installer;
for the direct menu, verify `python3-nautilus` is installed and restart Files.
If the output already exists, rename or move it before retrying.

### Terminal usage

From `context-menu/linux`, for example:

```sh
./sanitize_3mf.py "/path/to/model.3mf"
./sanitize_3mf.py "/path/to/model.3mf" --output "/path/to/fixed.3mf"
./sanitize_3mf.py --help
```

By default the original is preserved. The optional `--in-place` instead
overwrites it and creates `model.3mf.bak`; an existing backup with that name
may be overwritten. Use that option only if you intend to change the original.

### Uninstall

From `context-menu/linux`, run:

```sh
bash uninstall.sh
nautilus -q
```

Reopen Files after restarting it. This removes the per-user tool and menu
entries, not your `.3mf` files.

## Building and tests

To build the Windows x64 executable on Linux, install Go 1.27.3 or later and run
`context-menu/windows/build.sh` from the repository root. The build downloads
`go-winres` v0.3.3 and Go module dependencies if they are not cached. Python
with Pillow is only required to regenerate the included icon. The output is
`context-menu/dist/Sanitizador3MF.exe`. The included precompiled executable
was tested on Windows by the contributor; a rebuild from the recovered source
is not byte-identical and has not been tested on Windows.

Run each command from the repository root in a separate shell:

```sh
cd context-menu/linux && python3 -m unittest -v
cd context-menu/windows && go test ./...
```
