"""
test_scanner.py — Tests unitaires pour le scanner de fichiers.

Auteur : Bouchra
Date   : 2026-04-24
"""

import os
import pytest
from pathlib import Path

# Ajouter le dossier parent au path pour importer analyzer
import sys
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from analyzer.scanner import scan_project, get_project_name


# Chemin vers le projet fixture
FIXTURES_DIR = str(Path(__file__).resolve().parent / "fixtures" / "sample_project")


class TestScanProject:
    """Tests pour la fonction scan_project."""

    def test_scan_finds_python_files(self):
        """Vérifie que le scanner trouve les fichiers .py."""
        results = scan_project(FIXTURES_DIR, language="python", include_tests=True)
        
        # On doit trouver au moins models.py, main.py, broken_file.py
        paths = [r["path"] for r in results]
        assert any("models.py" in p for p in paths), f"models.py non trouvé dans {paths}"
        assert any("main.py" in p for p in paths), f"main.py non trouvé dans {paths}"

    def test_scan_returns_correct_structure(self):
        """Vérifie que chaque résultat a les bons champs."""
        results = scan_project(FIXTURES_DIR, language="python", include_tests=True)
        
        for r in results:
            assert "path" in r, "Champ 'path' manquant"
            assert "abs_path" in r, "Champ 'abs_path' manquant"
            assert "size_bytes" in r, "Champ 'size_bytes' manquant"
            assert r["size_bytes"] > 0, f"Taille invalide pour {r['path']}"

    def test_scan_nonexistent_dir_raises_error(self):
        """Vérifie qu'un dossier inexistant lève FileNotFoundError."""
        with pytest.raises(FileNotFoundError):
            scan_project("/chemin/qui/nexiste/pas")

    def test_scan_unsupported_language_raises_error(self):
        """Vérifie qu'un langage non supporté lève ValueError."""
        with pytest.raises(ValueError, match="non supporté"):
            scan_project(FIXTURES_DIR, language="cobol")

    def test_scan_ignores_pycache(self, tmp_path):
        """Vérifie que __pycache__ est ignoré."""
        # Créer une structure avec __pycache__
        (tmp_path / "good.py").write_text("x = 1\n")
        pycache = tmp_path / "__pycache__"
        pycache.mkdir()
        (pycache / "bad.cpython-311.pyc").write_text("compiled\n")
        # Un .py dans __pycache__ ne devrait pas être trouvé
        (pycache / "cached.py").write_text("y = 2\n")

        results = scan_project(str(tmp_path), language="python", include_tests=True)
        paths = [r["path"] for r in results]
        
        assert "good.py" in paths
        assert not any("__pycache__" in p for p in paths)


class TestGetProjectName:
    """Tests pour get_project_name."""

    def test_simple_path(self):
        assert get_project_name("/home/user/projects/chatnow") == "chatnow"

    def test_windows_path(self):
        name = get_project_name("C:\\Users\\bouchra\\Desktop\\forgegraph")
        assert name == "forgegraph"

    def test_trailing_slash(self):
        assert get_project_name("/home/user/projects/myapp/") == "myapp"
