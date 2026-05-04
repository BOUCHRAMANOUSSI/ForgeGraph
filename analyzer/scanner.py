"""
scanner.py — Scanner de fichiers source d'un projet.

Ce module parcourt récursivement un dossier de projet et retourne
la liste des fichiers source à analyser, en filtrant les dossiers
et fichiers non pertinents.

Auteur : Bouchra
Date   : 2026-04-24
"""

from __future__ import annotations

import os
import logging
from pathlib import Path

logger = logging.getLogger(__name__)


# ─────────────────────────────────────────────
# Dossiers à ignorer lors du scan
# ─────────────────────────────────────────────
IGNORED_DIRS: set[str] = {
    "__pycache__",
    ".git",
    ".svn",
    ".hg",
    ".venv",
    "venv",
    "env",
    ".env",
    "node_modules",
    ".tox",
    ".mypy_cache",
    ".pytest_cache",
    ".ruff_cache",
    "dist",
    "build",
    "egg-info",
    ".eggs",
    ".idea",
    ".vscode",
    "migrations",       # Alembic migrations (auto-générées)
    "__pypackages__",
}

# ─────────────────────────────────────────────
# Extensions de fichiers supportées par langage
# ─────────────────────────────────────────────
EXTENSIONS_BY_LANGUAGE: dict[str, set[str]] = {
    "python": {".py"},
    "javascript": {".js", ".jsx", ".mjs"},
    "typescript": {".ts", ".tsx"},
    "java": {".java"},
    "go": {".go"},
    "rust": {".rs"},
}

# Fichiers à toujours ignorer (même si l'extension correspond)
IGNORED_FILES: set[str] = {
    "__init__.py",   # Optionnel : on peut les inclure. Ici on les garde.
    "setup.py",
    "conftest.py",
}

# Taille maximale d'un fichier à analyser (éviter les fichiers générés)
MAX_FILE_SIZE_BYTES: int = 500_000  # 500 KB


def scan_project(
    project_path: str,
    language: str = "python",
    include_init: bool = True,
    include_tests: bool = False,
) -> list[dict[str, any]]:
    """
    Parcourt récursivement un dossier de projet et retourne la liste
    des fichiers source à analyser.

    Args:
        project_path  : Chemin absolu vers le dossier racine du projet.
        language      : Langage cible (détermine les extensions à scanner).
        include_init  : Si True, inclut les fichiers __init__.py.
        include_tests : Si True, inclut les fichiers de test (test_*.py, *_test.py).

    Returns:
        Liste de dictionnaires contenant :
        - "path"       : chemin relatif du fichier par rapport au projet
        - "abs_path"   : chemin absolu du fichier
        - "size_bytes" : taille du fichier en octets

    Raises:
        FileNotFoundError : Si le dossier project_path n'existe pas.
        ValueError        : Si le langage n'est pas supporté.
    """
    # ── Validation des entrées ──
    root = Path(project_path).resolve()
    if not root.exists():
        raise FileNotFoundError(f"Le dossier '{project_path}' n'existe pas.")
    if not root.is_dir():
        raise NotADirectoryError(f"'{project_path}' n'est pas un dossier.")

    extensions = EXTENSIONS_BY_LANGUAGE.get(language)
    if extensions is None:
        supported = ", ".join(sorted(EXTENSIONS_BY_LANGUAGE.keys()))
        raise ValueError(
            f"Langage '{language}' non supporté. Langages disponibles : {supported}"
        )

    logger.info(f"Scan du projet '{root}' pour le langage '{language}'...")

    # ── Parcours récursif ──
    found_files: list[dict[str, any]] = []

    for dirpath, dirnames, filenames in os.walk(root):
        # Filtrer les dossiers à ignorer (modifie dirnames in-place pour os.walk)
        dirnames[:] = [
            d for d in dirnames
            if d not in IGNORED_DIRS and not d.startswith(".")
        ]

        for filename in sorted(filenames):
            # Vérifier l'extension
            _, ext = os.path.splitext(filename)
            if ext not in extensions:
                continue

            # Filtrer __init__.py si demandé
            if not include_init and filename == "__init__.py":
                continue

            # Filtrer les fichiers de test si demandé
            if not include_tests:
                if filename.startswith("test_") or filename.endswith("_test.py"):
                    continue

            # Filtrer les fichiers ignorés
            if filename in IGNORED_FILES and filename != "__init__.py":
                continue

            # Chemin complet
            abs_path = Path(dirpath) / filename

            # Vérifier la taille
            try:
                size = abs_path.stat().st_size
            except OSError:
                logger.warning(f"Impossible de lire la taille de '{abs_path}', fichier ignoré.")
                continue

            if size > MAX_FILE_SIZE_BYTES:
                logger.warning(
                    f"Fichier '{abs_path}' trop volumineux ({size} octets > {MAX_FILE_SIZE_BYTES}), ignoré."
                )
                continue

            if size == 0:
                continue  # Fichiers vides

            # Chemin relatif par rapport à la racine du projet
            rel_path = abs_path.relative_to(root).as_posix()

            found_files.append({
                "path": rel_path,
                "abs_path": str(abs_path),
                "size_bytes": size,
            })

    logger.info(f"Scan terminé : {len(found_files)} fichiers {language} trouvés.")
    return found_files


def get_project_name(project_path: str) -> str:
    """
    Extrait le nom du projet à partir du chemin du dossier.
    
    Exemple :
        "/home/user/projects/chatnow" → "chatnow"
        "C:\\Users\\bouchra\\Desktop\\forgegraph" → "forgegraph"
    """
    return Path(project_path).resolve().name
