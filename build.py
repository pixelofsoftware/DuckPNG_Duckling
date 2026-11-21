#!/usr/bin/env python3
"""Zbuduj aplikację, przykład i testy wrappera libpng; komendy uruchomienia zapisz w budowa.json.

Skrypt na bazie build.py z szablonu konkursu DuckQuest (Fundacja Duckling, MIT). Zmiany:
dołączanie biblioteki libpng (--png albo automatyczne wyszukanie), cel "przyklad"
(przyklady/podstawowy.dk), kopia katalogu dane/ do katalogu budowy (pliki testowe)
i wyłącznie wariant natywny.
Nie pobiera i nie instaluje paczek.
"""

import argparse
import ctypes.util
import json
from pathlib import Path
import shutil
import subprocess


ROOT = Path(__file__).resolve().parent
ENTRIES = {"app": None, "tests": ROOT / "tests/testy.dk", "przyklad": ROOT / "przyklady/podstawowy.dk"}
REPORT = "budowa.json"
LIBRARY_CANDIDATES = (
    "/usr/lib/x86_64-linux-gnu/libpng16.so.16",
    "/usr/lib/aarch64-linux-gnu/libpng16.so.16",
    "/usr/lib64/libpng16.so.16",
    "/usr/lib/libpng16.so.16",
    "/opt/homebrew/lib/libpng16.dylib",
    "/usr/local/lib/libpng16.dylib",
    "/usr/local/lib/libpng16.so.16",
)
PKG_CONFIG_NAME = "libpng16"
FILE_NAMES = ("libpng16.so.16", "libpng16.so", "libpng16.dylib")
CTYPES_NAME = "png16"
INSTALL_HINT = ("zainstaluj libpng 1.6 (Ubuntu: sudo apt install libpng16-16t64; macOS: brew install libpng) "
                "albo wskaz plik biblioteki przez --png")


def execute(command, cwd):
    command = [str(part) for part in command]
    return subprocess.run(command, cwd=cwd, capture_output=True, text=True, timeout=180)


def find_tool(path, name, option):
    """Zwróć ścieżkę podaną wprost albo narzędzie z PATH (instalacja według tutoriala)."""
    if path is None:
        found = shutil.which(name)
        if found is None:
            raise ValueError(f"Nie znaleziono {name} w PATH. Zainstaluj Ducklinga według "
                             f"tutoriala albo wskaż narzędzie przez {option}.")
        path = Path(found)
    path = path.resolve()
    if not path.is_file():
        raise ValueError(f"Nie znaleziono {name}: {path}")
    return path


def find_library(explicit):
    """Plik biblioteki: podany wprost, z pkg-config, ze znanych miejsc albo z ctypes."""
    if explicit:
        if not explicit.is_file():
            raise ValueError(f"Nie znaleziono biblioteki {explicit}")
        return explicit.resolve()
    try:
        result = subprocess.run(["pkg-config", "--variable=libdir", PKG_CONFIG_NAME], capture_output=True, text=True)
        if result.returncode == 0:
            libdir = Path(result.stdout.strip())
            for name in FILE_NAMES:
                if (libdir / name).is_file():
                    return (libdir / name).resolve()
    except OSError:
        pass
    for candidate in LIBRARY_CANDIDATES:
        if Path(candidate).is_file():
            return Path(candidate).resolve()
    name = ctypes.util.find_library(CTYPES_NAME)
    if name and Path(name).is_file():
        return Path(name).resolve()
    raise ValueError(f"Nie znaleziono biblioteki - {INSTALL_HINT}")


def version(tool, option):
    result = execute([tool, option], ROOT)
    if result.returncode != 0:
        raise ValueError(f"{tool} {option} zwrócił kod {result.returncode}:\n{result.stderr}")
    return result.stdout


def prepare_output(output):
    """Usuń poprzednią budowę albo pusty katalog; katalogu z innymi plikami nie ruszaj."""
    if output.is_dir() and ((output / REPORT).is_file() or not any(output.iterdir())):
        shutil.rmtree(output)
    elif output.exists():
        raise ValueError(f"{output} nie jest katalogiem budowy; wybierz inny --output.")
    output.mkdir(parents=True)


def package(output, target):
    """Zwróć katalog pakietu: źródła aplikacji albo ich kopię z innym punktem wejścia."""
    if ENTRIES[target] is None:
        return ROOT / "app"
    path = output / f"pakiet-{target}" / "app"
    shutil.copytree(ROOT / "app", path)
    shutil.copy2(ENTRIES[target], path / "app.dk")
    return path


def build(args):
    targets = ("app", "przyklad", "tests") if args.target == "all" else (args.target,)
    duckc = find_tool(args.duckc, "duckc", "--duckc")
    library = find_library(args.png)
    report = {"ok": False, "tools": {}, "library": str(library), "compilation": {}, "commands": {}}
    report["tools"]["duckc"] = version(duckc, "--version-verbose")

    output = args.output.resolve()
    prepare_output(output)
    shutil.copytree(ROOT / "dane", output / "dane")
    try:
        for target in targets:
            source = package(output, target)
            name = f"{target}-native"
            artifacts = output / name
            command = [duckc, "compile_package", source, "-n", "app", "-a", artifacts,
                       "--custom-std-artifacts-path", output / "std",
                       "--additional-link-options", library]
            if args.std:
                command += ["--custom-std-path", args.std.resolve()]
            result = execute(command, output)
            report["compilation"][name] = result.stderr + result.stdout
            binary = artifacts / "package_llvm.exe"
            passed = result.returncode == 0 and binary.is_file()
            print(("PASS " if passed else "FAIL ") + name, flush=True)
            if not passed:
                raise ValueError(f"kompilacja {name} nie powiodła się.\n{result.stderr}{result.stdout}")
            report["commands"][name] = [str(binary)]
        report["ok"] = True
        print(f"biblioteka: {library}", flush=True)
    finally:
        text = json.dumps(report, ensure_ascii=False, indent=2) + "\n"
        (output / REPORT).write_text(text, encoding="utf-8")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--duckc", type=Path, help="Kompilator; domyślnie duckc z PATH.")
    parser.add_argument("--png", type=Path, help="Plik biblioteki libpng 1.6 (.so albo .dylib).")
    parser.add_argument("--std", type=Path,
                        help="Źródła zgodnej biblioteki standardowej, jeśli nie są ustawione w duckc.")
    parser.add_argument("--target", choices=("app", "przyklad", "tests", "all"), default="app")
    parser.add_argument("--output", type=Path, default=ROOT / "build",
                        help="Katalog wyników; poprzednia budowa w nim zostanie zastąpiona.")
    args = parser.parse_args()
    try:
        build(args)
    except (OSError, ValueError, subprocess.TimeoutExpired) as error:
        parser.exit(1, f"Błąd budowania: {error}\n")


if __name__ == "__main__":
    main()
