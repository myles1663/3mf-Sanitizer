"""Extensión de Nautilus: añade "Sanitizar 3MF" al menú contextual de archivos .3mf.

Requiere el paquete python3-nautilus. Se instala en
~/.local/share/nautilus-python/extensions/ mediante install.sh.
"""

from pathlib import Path

from gi.repository import GLib, GObject, Gio, Nautilus

SANITIZER = Path.home() / ".local" / "bin" / "sanitize-3mf"
MIME_3MF = {"model/3mf", "application/vnd.ms-package.3dmanufacturing-3dmodel+xml"}


def _local_3mf_path(file_info):
    if file_info.get_uri_scheme() != "file" or file_info.is_directory():
        return None
    location = file_info.get_location()
    path = location.get_path() if location else None
    if not path:
        return None
    if path.lower().endswith(".3mf") or file_info.get_mime_type() in MIME_3MF:
        return path
    return None


class Sanitize3mfMenuProvider(GObject.GObject, Nautilus.MenuProvider):
    def get_file_items(self, files):
        paths = [_local_3mf_path(file_info) for file_info in files]
        if not paths or None in paths:
            return []

        label = "Sanitizar 3MF" if len(paths) == 1 else f"Sanitizar {len(paths)} archivos 3MF"
        item = Nautilus.MenuItem(
            name="Sanitize3mf::sanitize",
            label=label,
            tip="Corrige ajustes incompatibles en proyectos de MakerWorld/Bambu Lab",
        )
        item.connect("activate", self._on_activate, paths)
        return [item]

    def get_background_items(self, current_folder):
        return []

    def _on_activate(self, _item, paths):
        try:
            Gio.Subprocess.new([str(SANITIZER), "--notify", "--", *paths], Gio.SubprocessFlags.NONE)
        except GLib.Error as error:
            print(f"Sanitizar 3MF: no se pudo ejecutar {SANITIZER}: {error.message}")
