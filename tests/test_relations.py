"""
test_relations.py — Tests unitaires pour extraction des relations.

Auteur : Bouchra
Date   : 2026-04-24
"""

import pytest
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from analyzer.parser_python import parse_python_file
from analyzer.relations import extract_relations


# Chemin vers les fixtures
FIXTURES_DIR = Path(__file__).resolve().parent / "fixtures" / "sample_project"
MODELS_FILE = str(FIXTURES_DIR / "models.py")
MAIN_FILE = str(FIXTURES_DIR / "main.py")


class TestExtractRelations:
    """Tests pour extraction des relations entre entités."""

    def test_import_relations(self):
        """Vérifie la détection des relations d'import."""
        models_analysis = parse_python_file(MODELS_FILE)
        models_analysis.path = "models.py"
        
        main_analysis = parse_python_file(MAIN_FILE)
        main_analysis.path = "main.py"
        
        relations = extract_relations([models_analysis, main_analysis])
        
        # main.py importe User et AdminUser de models.py
        import_relations = [r for r in relations if r.type == "import"]
        assert len(import_relations) > 0
        
        # Vérifier qu'il y a une relation User → main.py
        user_imports = [r for r in import_relations if r.to_entity == "User"]
        assert len(user_imports) > 0
        assert user_imports[0].to_file == "models.py"

    def test_inheritance_relations(self):
        """Vérifie la détection des relations d'héritage."""
        models_analysis = parse_python_file(MODELS_FILE)
        models_analysis.path = "models.py"
        
        relations = extract_relations([models_analysis])
        
        # AdminUser hérite de User
        inheritance_relations = [r for r in relations if r.type == "inheritance"]
        assert len(inheritance_relations) > 0
        
        admin_inherits = [r for r in inheritance_relations if r.from_entity == "AdminUser"]
        assert len(admin_inherits) > 0
        assert admin_inherits[0].to_entity == "User"
        assert admin_inherits[0].to_file == "models.py"

    def test_empty_file_list(self):
        """Vérifie le comportement avec une liste vide."""
        relations = extract_relations([])
        assert relations == []

    def test_unresolved_parent_class(self):
        """Vérifie les classes parentes non trouvées dans le projet."""
        models_analysis = parse_python_file(MODELS_FILE)
        models_analysis.path = "models.py"
        
        relations = extract_relations([models_analysis])
        
        # User hérite de BaseModel (qui n'existe pas dans les fixtures)
        # on ne doit pas avoir de crash
        inheritance_relations = [r for r in relations if r.type == "inheritance"]
        # Il peut y avoir des relations non résolues (to_file = None)
        unresolved = [r for r in inheritance_relations if r.to_file is None]
        # C'est OK, les bibliothèques externes n'ont pas to_file résolu
