"""
test_parser.py — Tests unitaires pour le parser Python.

Auteur : Bouchra
Date   : 2026-04-24
"""

import pytest
from pathlib import Path

import sys
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from analyzer.parser_python import parse_python_file


# Chemin vers les fixtures
FIXTURES_DIR = Path(__file__).resolve().parent / "fixtures" / "sample_project"
MODELS_FILE = str(FIXTURES_DIR / "models.py")
MAIN_FILE = str(FIXTURES_DIR / "main.py")
BROKEN_FILE = str(FIXTURES_DIR / "broken_file.py")


class TestParseClasses:
    """Tests d'extraction des classes."""

    def test_finds_all_classes(self):
        """Vérifie qu'on trouve les 2 classes (User, AdminUser)."""
        result = parse_python_file(MODELS_FILE)
        class_names = [c.name for c in result.classes]
        
        assert "User" in class_names
        assert "AdminUser" in class_names
        assert len(result.classes) == 2

    def test_class_has_methods(self):
        """Vérifie que la classe User a ses méthodes."""
        result = parse_python_file(MODELS_FILE)
        user_cls = next(c for c in result.classes if c.name == "User")
        method_names = [m.name for m in user_cls.methods]

        assert "full_name" in method_names
        assert "is_adult" in method_names
        assert "validate_email" in method_names

    def test_class_inheritance(self):
        """Vérifie que AdminUser hérite de User."""
        result = parse_python_file(MODELS_FILE)
        admin_cls = next(c for c in result.classes if c.name == "AdminUser")
        
        assert "User" in admin_cls.base_classes

    def test_class_decorators(self):
        """Vérifie que @dataclass est détecté sur User."""
        result = parse_python_file(MODELS_FILE)
        user_cls = next(c for c in result.classes if c.name == "User")
        
        assert "dataclass" in user_cls.decorators

    def test_class_docstring(self):
        """Vérifie la docstring de la classe User."""
        result = parse_python_file(MODELS_FILE)
        user_cls = next(c for c in result.classes if c.name == "User")
        
        assert user_cls.docstring is not None
        assert "utilisateur" in user_cls.docstring.lower()

    def test_method_decorators(self):
        """Vérifie que @property et @staticmethod sont détectés."""
        result = parse_python_file(MODELS_FILE)
        user_cls = next(c for c in result.classes if c.name == "User")
        
        is_adult = next(m for m in user_cls.methods if m.name == "is_adult")
        assert "property" in is_adult.decorators

        validate = next(m for m in user_cls.methods if m.name == "validate_email")
        assert "staticmethod" in validate.decorators

    def test_async_method(self):
        """Vérifie la détection des méthodes async."""
        result = parse_python_file(MODELS_FILE)
        admin_cls = next(c for c in result.classes if c.name == "AdminUser")
        
        revoke = next(m for m in admin_cls.methods if m.name == "revoke_access")
        assert revoke.is_async is True


class TestParseFunctions:
    """Tests d'extraction des fonctions top-level."""

    def test_finds_all_functions(self):
        """Vérifie qu'on trouve les fonctions hors-classe."""
        result = parse_python_file(MODELS_FILE)
        func_names = [f.name for f in result.functions]

        assert "hash_password" in func_names
        assert "fetch_user_from_db" in func_names
        assert "process_batch" in func_names
        assert len(result.functions) == 3

    def test_function_args(self):
        """Vérifie les arguments de hash_password."""
        result = parse_python_file(MODELS_FILE)
        hash_fn = next(f for f in result.functions if f.name == "hash_password")
        
        arg_names = [a.name for a in hash_fn.args]
        assert "raw_password" in arg_names
        assert "salt" in arg_names

    def test_function_return_type(self):
        """Vérifie le type de retour de hash_password."""
        result = parse_python_file(MODELS_FILE)
        hash_fn = next(f for f in result.functions if f.name == "hash_password")
        
        assert hash_fn.return_type == "str"

    def test_async_function(self):
        """Vérifie la détection d'une fonction async."""
        result = parse_python_file(MODELS_FILE)
        fetch_fn = next(f for f in result.functions if f.name == "fetch_user_from_db")
        
        assert fetch_fn.is_async is True

    def test_function_default_values(self):
        """Vérifie les valeurs par défaut des arguments."""
        result = parse_python_file(MODELS_FILE)
        hash_fn = next(f for f in result.functions if f.name == "hash_password")
        
        salt_arg = next(a for a in hash_fn.args if a.name == "salt")
        assert salt_arg.default == '"default"'


class TestParseImports:
    """Tests d'extraction des imports."""

    def test_finds_imports(self):
        """Vérifie qu'on trouve les imports."""
        result = parse_python_file(MODELS_FILE)
        
        assert len(result.imports) > 0

    def test_simple_import(self):
        """Vérifie un import simple (import os)."""
        result = parse_python_file(MODELS_FILE)
        
        os_imports = [i for i in result.imports if i.module == "os"]
        assert len(os_imports) > 0
        assert os_imports[0].type == "import"

    def test_from_import(self):
        """Vérifie un from import (from dataclasses import dataclass)."""
        result = parse_python_file(MODELS_FILE)
        
        dc_imports = [i for i in result.imports if i.module == "dataclasses"]
        assert len(dc_imports) > 0
        assert "dataclass" in dc_imports[0].names


class TestParseGlobalVariables:
    """Tests d'extraction des variables globales."""

    def test_finds_global_variables(self):
        """Vérifie qu'on trouve les constantes de module."""
        result = parse_python_file(MODELS_FILE)
        var_names = [v.name for v in result.global_variables]

        assert "MAX_RETRIES" in var_names
        assert "DEFAULT_TIMEOUT" in var_names
        assert "_PRIVATE_CONSTANT" in var_names

    def test_variable_values(self):
        """Vérifie les valeurs des variables."""
        result = parse_python_file(MODELS_FILE)
        max_retries = next(v for v in result.global_variables if v.name == "MAX_RETRIES")
        
        assert max_retries.value == "3"


class TestErrorHandling:
    """Tests de gestion des erreurs."""

    def test_broken_file_does_not_crash(self):
        """Vérifie que le parser ne crashe PAS sur un fichier avec erreur de syntaxe."""
        result = parse_python_file(BROKEN_FILE)
        
        assert result.error is not None
        assert "SyntaxError" in result.error

    def test_nonexistent_file(self):
        """Vérifie le comportement sur un fichier inexistant."""
        result = parse_python_file("/fichier/qui/nexiste/pas.py")
        
        assert result.error is not None

    def test_broken_file_has_metadata(self):
        """Même en erreur, on a les métadonnées de base."""
        result = parse_python_file(BROKEN_FILE)
        
        assert result.total_lines > 0
