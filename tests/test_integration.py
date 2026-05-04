"""
test_integration.py — Tests d'intégration E2E.

Test le workflow complet : scan → parse → extract_relations → analyze_project.

Auteur : Bouchra
Date   : 2026-04-24
"""

import json
import pytest
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from analyzer import analyze_project


# Chemin vers les fixtures
FIXTURES_DIR = Path(__file__).resolve().parent / "fixtures" / "sample_project"


class TestAnalyzeProject:
    """Tests d'intégration E2E pour analyze_project()."""

    def test_analyze_project_returns_dict(self):
        """Vérifie que analyze_project retourne un dictionnaire."""
        result = analyze_project(str(FIXTURES_DIR))
        
        assert isinstance(result, dict)

    def test_analyze_project_has_required_fields(self):
        """Vérifie la présence de tous les champs requis."""
        result = analyze_project(str(FIXTURES_DIR))
        
        assert "project_name" in result
        assert "language" in result
        assert "analyzed_at" in result
        assert "stats" in result
        assert "files" in result
        assert "relations" in result

    def test_analyze_project_stats(self):
        """Vérifie les statistiques calculées."""
        result = analyze_project(str(FIXTURES_DIR))
        stats = result["stats"]
        
        assert "total_files" in stats
        assert "total_classes" in stats
        assert "total_functions" in stats
        assert "total_methods" in stats
        assert "total_imports" in stats
        assert "files_with_errors" in stats
        
        # Au moins 2 fichiers sans erreur dans les fixtures
        assert stats["total_files"] >= 2
        assert stats["total_classes"] >= 2
        assert stats["total_functions"] >= 3

    def test_analyze_project_json_serializable(self):
        """Vérifie que le résultat est sérialisable en JSON."""
        result = analyze_project(str(FIXTURES_DIR))
        
        # Doit être JSON-serializable
        json_str = json.dumps(result)
        assert len(json_str) > 0

    def test_analyze_project_nonexistent_dir(self):
        """Vérifie l'erreur sur un dossier inexistant."""
        with pytest.raises(FileNotFoundError):
            analyze_project("/chemin/qui/nexiste/pas")

    def test_analyze_project_project_name(self):
        """Vérifie que le nom du projet est extrait."""
        result = analyze_project(str(FIXTURES_DIR))
        
        assert result["project_name"] == "sample_project"

    def test_analyze_project_language(self):
        """Vérifie que le langage est enregistré."""
        result = analyze_project(str(FIXTURES_DIR), language="python")
        
        assert result["language"] == "python"

    def test_analyze_project_files_have_paths(self):
        """Vérifie que les fichiers analysés ont des chemins relatifs."""
        result = analyze_project(str(FIXTURES_DIR))
        
        assert len(result["files"]) > 0
        for file_info in result["files"]:
            assert "path" in file_info
            assert file_info["path"] != ""

    def test_analyze_project_relations_count(self):
        """Vérifie qu'il y a des relations détectées."""
        result = analyze_project(str(FIXTURES_DIR))
        
        # Au minimum : main.py importe de models.py + AdminUser hérite de User
        assert len(result["relations"]) >= 2

    def test_analyze_project_output_matches_schema(self):
        """Vérifie que la sortie respecte le schéma JSON défini."""
        result = analyze_project(str(FIXTURES_DIR))
        
        # Vérifier la structure du premier fichier
        if result["files"]:
            file_info = result["files"][0]
            assert isinstance(file_info["path"], str)
            assert isinstance(file_info["size_bytes"], int)
            assert isinstance(file_info["total_lines"], int)
            assert isinstance(file_info["classes"], list)
            assert isinstance(file_info["functions"], list)
            assert isinstance(file_info["imports"], list)
            assert isinstance(file_info["global_variables"], list)

    def test_analyzed_at_is_iso_format(self):
        """Vérifie que analyzed_at est en format ISO 8601."""
        result = analyze_project(str(FIXTURES_DIR))
        
        # Format ISO8601 avec T et Z
        assert "T" in result["analyzed_at"]
        assert result["analyzed_at"].endswith("Z") or "+" in result["analyzed_at"]
