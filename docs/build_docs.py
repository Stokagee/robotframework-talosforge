#!/usr/bin/env python3
"""
Build skript pro TalosForge dokumentaci.

Tento skript automaticky:
1. Nainstaluje závislosti pro dokumentaci
2. Zkontroluje existenci docstringů
3. Builduje HTML dokumentaci
4. Otevře dokumentaci v prohlížeči

Použití:
    python docs/build_docs.py
"""

import os
import subprocess
import sys
import webbrowser
from pathlib import Path

# Barvy pro terminál
class Colors:
    GREEN = '\033[92m'
    BLUE = '\033[94m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'

    @classmethod
    def print_success(cls, msg):
        print(f"{cls.GREEN}[OK]{cls.ENDC} {msg}")

    @classmethod
    def print_info(cls, msg):
        print(f"{cls.BLUE}[INFO]{cls.ENDC} {msg}")

    @classmethod
    def print_warning(cls, msg):
        print(f"{cls.YELLOW}[WARN]{cls.ENDC} {msg}")

    @classmethod
    def print_error(cls, msg):
        print(f"{cls.RED}[ERROR]{cls.ENDC} {msg}")

    @classmethod
    def print_header(cls, msg):
        print(f"\n{cls.BOLD}{cls.BLUE}=== {msg} ==={cls.ENDC}")


def run_command(cmd, description):
    """Spustí příkaz a zobrazí výstup."""
    print(f"\n{Colors.BOLD}> {description}{Colors.ENDC}")
    print(f"  {Colors.YELLOW}->{Colors.ENDC} {cmd}")

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, shell=True, check=False)
        if result.returncode == 0:
            Colors.print_success("Hotovo")
            if result.stdout.strip():
                print(result.stdout)
            if result.stderr.strip():
                print(result.stderr)
        else:
            Colors.print_warning(f"Varování při spuštění (returncode={result.returncode})")
            if result.stdout.strip():
                print(result.stdout)
            if result.stderr.strip():
                print(result.stderr)
    except Exception as e:
        Colors.print_error(f"Chyba: {e}")
        sys.exit(1)


def check_project_root():
    """Zkontroluje, zda jsme v kořenovém adresáři projektu."""
    root_indicators = [
        "talosforge",
        "pyproject.toml",
        "README.md"
    ]

    current = Path.cwd()
    parent = current.parent

    # Pokud nejsme v rootu, zkusíme o úroveň výš
    if not all((current / ind).exists() for ind in root_indicators):
        if all((parent / ind).exists() for ind in root_indicators):
            os.chdir(parent)
            Colors.print_info("Přepnut do kořenového adresáře projektu")
            return

    # Kontrola
    if all((Path(ind).exists() for ind in root_indicators)):
        Colors.print_success("V kořenovém adresáři projektu")
    else:
        Colors.print_error("Není v kořenovém adresáři projektu (chybí: talosforge/, pyproject.toml, README.md)")
        sys.exit(1)


def install_dependencies():
    """Nainstalí závislosti pro dokumentaci."""
    docs_dir = Path(__file__).parent
    req_file = docs_dir / "requirements.txt"

    if not req_file.exists():
        Colors.print_error(f"requirements.txt nenalezen v {docs_dir}")
        sys.exit(1)

    Colors.print_info("Instaluji závislosti pro dokumentaci...")
    run_command(
        f'pip install -r "{req_file}"',
        "Instalace závislostí"
    )


def check_docstrings():
    """Zkontroluje přítomnost docstringů."""
    Colors.print_info("Kontroluji docstringy...")

    project_root = Path(__file__).parent.parent

    # Hlavní soubory ke kontrole
    files_to_check = [
        "talosforge/__init__.py",
        "talosforge/core/generator.py",
        "talosforge/schema/loader.py",
        "talosforge/core/ai_generator.py",
    ]

    missing_docs = []

    for file_path in files_to_check:
        full_path = project_root / file_path
        if not full_path.exists():
            missing_docs.append(f"{file_path} (soubor neexistuje)")
            continue

        with open(full_path, 'r', encoding='utf-8') as f:
            content = f.read()
            # Základní kontrola - hledáme '"""' v souboru
            if '"""' not in content:
                missing_docs.append(f"{file_path} (chybí docstringy)")

    if missing_docs:
        Colors.print_warning(f"Některé soubory mají chybějící docstrings:")
        for doc in missing_docs:
            print(f"  - {doc}")
    else:
        Colors.print_success("Všechny soubory mají docstrings")


def build_docs():
    """Builduje HTML dokumentaci."""
    docs_dir = Path(__file__).parent

    # Vytvořit _build adresář
    build_dir = docs_dir / "_build"
    build_dir.mkdir(exist_ok=True)

    Colors.print_info("Builduji HTML dokumentaci...")
    run_command(
        f'sphinx-build -b html "{docs_dir}" "{build_dir}/html"',
        "Sphinx build"
    )

    return build_dir / "html" / "index.html"


def open_docs(html_file):
    """Otevře dokumentaci v prohlížeči."""
    Colors.print_info("Otevírám dokumentaci v prohlížeči...")

    html_file = Path(html_file).resolve()
    if not html_file.exists():
        Colors.print_error(f"Dokumentace nenalezena: {html_file}")
        return

    # Otevření v prohlížeči
    if sys.platform == "win32":
        os.startfile(html_file)
    else:
        # Pro Linux/mac použijeme webbrowser
        try:
            webbrowser.open(str(html_file))
        except Exception as e:
            Colors.print_warning(f"Nepodařilo otevřít automaticky: {e}")
            Colors.print_info(f"Otevřete v prohlížeči: {html_file}")

    Colors.print_success(f"Dokumentace otevřena: {html_file}")


def main():
    """Hlavní funkce build skriptu."""
    print("""
    ==================================================
    TalosForge - Build Dokumentace
    Automatický build skript
    ==================================================
    """)

    # Zkontroluj projekt
    check_project_root()

    # Nainstaluj závislosti
    install_dependencies()

    # Zkontroluj docstrings
    check_docstrings()

    # Build dokumentace
    index_html = build_docs()

    # Otevři dokumentaci
    open_docs(index_html)

    print(f"\n{Colors.BOLD}{Colors.GREEN}============================================={Colors.ENDC}")
    print(f"{Colors.GREEN}Dokumentace úspěšně vygenerována a otevřena!{Colors.ENDC}")
    print(f"{Colors.BOLD}{Colors.GREEN}============================================={Colors.ENDC}\n")


if __name__ == "__main__":
    main()
