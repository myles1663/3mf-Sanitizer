#!/usr/bin/env python3
"""Sanitiza proyectos .3mf de MakerWorld y Bambu Lab.

Sustituye -1 por 0 en `raft_first_layer_expansion` y `tree_support_wall_count`,
valores incompatibles con algunos programas de impresión 3D.
Por defecto crea `<nombre>_sanitizado.3mf` junto al original sin modificarlo.
"""

from __future__ import annotations

import argparse
import os
import re
import shutil
import subprocess
import sys
import tempfile
import zipfile
from dataclasses import dataclass, field
from pathlib import Path

APP_NAME = "Sanitizador 3MF"
DEFAULT_SUFFIX = "_sanitizado"
FIXED_KEYS = ("raft_first_layer_expansion", "tree_support_wall_count")
TEXT_SUFFIXES = (".config", ".json", ".xml")

_KEYS = "|".join(FIXED_KEYS)
_PATTERNS = (
    # JSON: "clave": "-1" o "clave": -1.
    (re.compile(rf'("(?:{_KEYS})"\s*:\s*)(?:"-1"|-1(?![0-9.eE]))'), r'\g<1>"0"'),
    # INI: clave = -1
    (re.compile(rf"(?m)^([ \t]*(?:{_KEYS})[ \t]*=[ \t]*)-1(?=[ \t\r]*$)"), r"\g<1>0"),
    # XML de ajustes por objeto: <metadata key="clave" value="-1"/>
    (re.compile(rf'(\bkey\s*=\s*"(?:{_KEYS})"\s+value\s*=\s*")-1(")'), r"\g<1>0\g<2>"),
)
_KEY_BYTES = tuple(key.encode() for key in FIXED_KEYS)


class SanitizeError(Exception):
    pass


@dataclass
class SanitizeResult:
    source: Path
    output: Path | None = None
    fixes: dict[str, int] = field(default_factory=dict)

    @property
    def total_fixes(self) -> int:
        return sum(self.fixes.values())


def sanitize_text(text: str) -> tuple[str, int]:
    total = 0
    for pattern, replacement in _PATTERNS:
        text, count = pattern.subn(replacement, text)
        total += count
    return text, total


def _sanitize_entry(data: bytes) -> tuple[bytes, int]:
    if not any(key in data for key in _KEY_BYTES):
        return data, 0
    try:
        text = data.decode("utf-8")
    except UnicodeDecodeError:
        return data, 0
    text, count = sanitize_text(text)
    return (text.encode("utf-8"), count) if count else (data, 0)


def _should_scan(info: zipfile.ZipInfo) -> bool:
    return not info.is_dir() and info.filename.lower().endswith(TEXT_SUFFIXES)


def _copy_info(info: zipfile.ZipInfo) -> zipfile.ZipInfo:
    copy = zipfile.ZipInfo(info.filename, info.date_time)
    copy.compress_type = info.compress_type
    copy.create_system = info.create_system
    copy.external_attr = info.external_attr
    copy.comment = info.comment
    return copy


def _write_archive(
    source: Path, destination: Path, replacements: dict[str, bytes], *, overwrite: bool
) -> None:
    fd, tmp_name = tempfile.mkstemp(prefix=f".{destination.stem}.", suffix=".tmp", dir=destination.parent)
    os.close(fd)
    tmp = Path(tmp_name)
    try:
        with zipfile.ZipFile(source) as zin, zipfile.ZipFile(tmp, "w", allowZip64=True) as zout:
            zout.comment = zin.comment
            for info in zin.infolist():
                out_info = _copy_info(info)
                if info.filename in replacements:
                    zout.writestr(out_info, replacements[info.filename])
                elif info.is_dir():
                    zout.writestr(out_info, b"")
                else:
                    with zin.open(info) as src, zout.open(
                        out_info, "w", force_zip64=info.file_size > zipfile.ZIP64_LIMIT
                    ) as dst:
                        shutil.copyfileobj(src, dst, 1024 * 1024)

        with zipfile.ZipFile(tmp) as check:
            bad_entry = check.testzip()
        if bad_entry is not None:
            raise SanitizeError(f"El archivo generado está dañado ({bad_entry})")

        shutil.copymode(source, tmp)
        if overwrite:
            os.replace(tmp, destination)
        else:
            try:
                os.link(tmp, destination)
            except FileExistsError as error:
                raise SanitizeError(
                    f"Ya existe el archivo de salida: {destination}. El original no se ha modificado."
                ) from error
            tmp.unlink()
    except BaseException:
        tmp.unlink(missing_ok=True)
        raise


def default_output_path(source: Path, suffix: str = DEFAULT_SUFFIX) -> Path:
    return source.with_name(f"{source.stem}{suffix}{source.suffix}")


def sanitize_3mf(
    source: str | os.PathLike[str],
    output: str | os.PathLike[str] | None = None,
    *,
    in_place: bool = False,
    suffix: str = DEFAULT_SUFFIX,
) -> SanitizeResult:
    """Sanitiza un .3mf. Si no hay nada que corregir no escribe ningún archivo."""
    source = Path(source).expanduser().absolute()
    if not source.is_file():
        raise SanitizeError("El archivo no existe")
    if source.suffix.lower() != ".3mf":
        raise SanitizeError("No es un archivo .3mf")
    if not zipfile.is_zipfile(source):
        raise SanitizeError("No es un 3MF válido (no es un ZIP)")

    result = SanitizeResult(source)
    replacements: dict[str, bytes] = {}
    try:
        with zipfile.ZipFile(source) as archive:
            for info in archive.infolist():
                if not _should_scan(info):
                    continue
                data, count = _sanitize_entry(archive.read(info))
                if count:
                    replacements[info.filename] = data
                    result.fixes[info.filename] = count
    except (zipfile.BadZipFile, zipfile.LargeZipFile, NotImplementedError) as error:
        raise SanitizeError(f"No se pudo leer el 3MF: {error}") from error

    if not replacements:
        return result

    if in_place:
        destination = source
        shutil.copy2(source, source.with_name(source.name + ".bak"))
    else:
        destination = Path(output).expanduser().absolute() if output else default_output_path(source, suffix)
        if destination == source:
            raise SanitizeError("El archivo de salida no puede ser el original (usa --in-place)")

    try:
        _write_archive(source, destination, replacements, overwrite=in_place)
    except (zipfile.BadZipFile, zipfile.LargeZipFile, NotImplementedError) as error:
        raise SanitizeError(f"No se pudo reescribir el 3MF: {error}") from error
    result.output = destination
    return result


def _plural(count: int, singular: str, plural: str) -> str:
    return f"{count} {singular if count == 1 else plural}"


def _describe(result: SanitizeResult) -> str:
    if result.output is None:
        return f"{result.source.name}: no necesitaba cambios"
    fixes = _plural(result.total_fixes, "ajuste corregido", "ajustes corregidos")
    return f"{result.source.name}: {fixes} → {result.output.name}"


def notify(summary: str, body: str, error: bool = False) -> None:
    if shutil.which("notify-send"):
        command = ["notify-send", "-a", APP_NAME, "-i", "dialog-error" if error else "emblem-ok-symbolic"]
        if error:
            command += ["-u", "critical"]
        try:
            if subprocess.run(command + [summary, body], check=False, timeout=10).returncode == 0:
                return
        except (OSError, subprocess.TimeoutExpired):
            pass
    if shutil.which("zenity"):
        kind = "--error" if error else "--info"
        subprocess.run(["zenity", kind, "--title", APP_NAME, "--no-markup", "--text", f"{summary}\n\n{body}"],
                       check=False)


def _notify_summary(results: list[SanitizeResult], errors: list[tuple[str, str]]) -> None:
    lines = [_describe(result) for result in results] + [f"{name}: {message}" for name, message in errors]
    sanitized = sum(1 for result in results if result.output)
    if len(lines) == 1:
        if errors:
            summary = "No se pudo sanitizar el 3MF"
        elif sanitized:
            summary = "3MF sanitizado"
        else:
            summary = "El 3MF ya era compatible"
    else:
        parts = [_plural(sanitized, "sanitizado", "sanitizados"),
                 _plural(len(results) - sanitized, "sin cambios", "sin cambios")]
        if errors:
            parts.append(_plural(len(errors), "error", "errores"))
        summary = f"{len(lines)} archivos: " + ", ".join(parts)
    notify(summary, "\n".join(lines), error=bool(errors))


def _nautilus_selection() -> list[str]:
    selected = os.environ.get("NAUTILUS_SCRIPT_SELECTED_FILE_PATHS", "")
    return [line for line in selected.splitlines() if line]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Corrige raft_first_layer_expansion y tree_support_wall_count = -1 en archivos .3mf "
        "para que sean compatibles con programas de impresión 3D.",
    )
    parser.add_argument("files", nargs="*", metavar="ARCHIVO.3mf")
    parser.add_argument("-o", "--output", help="ruta de salida (solo con un archivo)")
    parser.add_argument("--in-place", action="store_true", help="sobrescribe el original y guarda una copia .bak")
    parser.add_argument("--suffix", default=DEFAULT_SUFFIX, help=f"sufijo del archivo generado (por defecto {DEFAULT_SUFFIX})")
    parser.add_argument("--notify", action="store_true", help="muestra el resultado como notificación de escritorio")
    args = parser.parse_args(argv)

    files = (_nautilus_selection() if args.notify else []) or args.files
    if not files:
        if args.notify:
            notify("No se pudo sanitizar el 3MF", "No hay ningún archivo seleccionado", error=True)
        parser.error("indica al menos un archivo .3mf")
    if args.output and (len(files) != 1 or args.in_place):
        parser.error("--output solo admite un archivo y no se combina con --in-place")

    results: list[SanitizeResult] = []
    errors: list[tuple[str, str]] = []
    for file in files:
        try:
            result = sanitize_3mf(file, args.output, in_place=args.in_place, suffix=args.suffix)
        except (SanitizeError, OSError) as error:
            message = error.strerror if isinstance(error, OSError) and error.strerror else str(error)
            errors.append((Path(file).name, message))
            print(f"[ERROR] {file}: {message}", file=sys.stderr)
            continue
        results.append(result)
        print(f"[OK] {_describe(result)}")
        for entry, count in result.fixes.items():
            print(f"     {entry}: {count}")

    if args.notify:
        _notify_summary(results, errors)
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
