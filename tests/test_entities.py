"""
test_entities.py — Tests pour les modèles de données.

Auteur : Bouchra
Date   : 2026-04-24
"""

import pytest
from datetime import datetime
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from analyzer.entities import (
    FunctionArg,
    FunctionEntity,
    ClassEntity,
    ImportEntity,
    GlobalVariable,
    FileAnalysis,
    ProjectAnalysis,
    Relation,
)


class TestFunctionArg:
    """Tests pour FunctionArg."""

    def test_create_simple_arg(self):
        """Crée un argument simple."""
        arg = FunctionArg(name="x")
        assert arg.name == "x"
        assert arg.type is None
        assert arg.default is None

    def test_create_typed_arg(self):
        """Crée un argument typé."""
        arg = FunctionArg(name="age", type="int")
        assert arg.name == "age"
        assert arg.type == "int"


class TestFunctionEntity:
    """Tests pour FunctionEntity."""

    def test_create_simple_function(self):
        """Crée une fonction simple."""
        func = FunctionEntity(name="greet")
        assert func.name == "greet"
        assert func.is_async is False
        assert len(func.args) == 0

    def test_create_async_function(self):
        """Crée une fonction async."""
        func = FunctionEntity(name="fetch", is_async=True)
        assert func.is_async is True

    def test_function_with_args(self):
        """Crée une fonction avec des arguments."""
        args = [
            FunctionArg(name="x", type="int"),
            FunctionArg(name="y", type="str", default='"default"'),
        ]
        func = FunctionEntity(name="process", args=args)
        assert len(func.args) == 2
        assert func.args[0].name == "x"

    def test_function_with_decorators(self):
        """Crée une fonction décorée."""
        func = FunctionEntity(
            name="cached",
            decorators=["lru_cache", "property"]
        )
        assert "property" in func.decorators


class TestClassEntity:
    """Tests pour ClassEntity."""

    def test_create_simple_class(self):
        """Crée une classe simple."""
        cls = ClassEntity(name="User")
        assert cls.name == "User"
        assert len(cls.methods) == 0
        assert len(cls.base_classes) == 0

    def test_class_with_methods(self):
        """Crée une classe avec des méthodes."""
        methods = [
            FunctionEntity(name="__init__"),
            FunctionEntity(name="save"),
        ]
        cls = ClassEntity(name="User", methods=methods)
        assert len(cls.methods) == 2

    def test_class_with_inheritance(self):
        """Crée une classe avec héritage."""
        cls = ClassEntity(
            name="AdminUser",
            base_classes=["User", "Mixin"]
        )
        assert "User" in cls.base_classes

    def test_class_with_decorators(self):
        """Crée une classe décorée."""
        cls = ClassEntity(
            name="Config",
            decorators=["dataclass", "frozen"]
        )
        assert "dataclass" in cls.decorators


class TestImportEntity:
    """Tests pour ImportEntity."""

    def test_simple_import(self):
        """Crée un import simple."""
        imp = ImportEntity(type="import", module="os")
        assert imp.type == "import"
        assert imp.module == "os"
        assert len(imp.names) == 0

    def test_from_import(self):
        """Crée un from import."""
        imp = ImportEntity(
            type="from",
            module="collections",
            names=["defaultdict", "Counter"]
        )
        assert imp.type == "from"
        assert "Counter" in imp.names


class TestGlobalVariable:
    """Tests pour GlobalVariable."""

    def test_create_variable(self):
        """Crée une variable globale."""
        var = GlobalVariable(name="MAX_RETRIES", value="3")
        assert var.name == "MAX_RETRIES"
        assert var.value == "3"


class TestFileAnalysis:
    """Tests pour FileAnalysis."""

    def test_create_file_analysis(self):
        """Crée une analyse de fichier."""
        fa = FileAnalysis(path="models.py", size_bytes=1000)
        assert fa.path == "models.py"
        assert fa.size_bytes == 1000
        assert len(fa.classes) == 0

    def test_file_with_entities(self):
        """Crée une analyse avec des entités."""
        cls = ClassEntity(name="User")
        func = FunctionEntity(name="main")
        fa = FileAnalysis(
            path="main.py",
            classes=[cls],
            functions=[func]
        )
        assert len(fa.classes) == 1
        assert len(fa.functions) == 1

    def test_file_with_error(self):
        """Crée une analyse avec erreur."""
        fa = FileAnalysis(
            path="broken.py",
            error="SyntaxError: invalid syntax"
        )
        assert fa.error is not None


class TestProjectAnalysis:
    """Tests pour ProjectAnalysis."""

    def test_create_project_analysis(self):
        """Crée une analyse de projet."""
        pa = ProjectAnalysis(project_name="myapp")
        assert pa.project_name == "myapp"
        assert pa.language == "python"

    def test_project_stats(self):
        """Vérifie les statistiques du projet."""
        cls1 = ClassEntity(name="User")
        cls2 = ClassEntity(name="Admin")
        func1 = FunctionEntity(name="setup")
        
        fa1 = FileAnalysis(
            path="models.py",
            classes=[cls1, cls2],
            functions=[func1]
        )
        
        pa = ProjectAnalysis(
            project_name="test",
            files=[fa1]
        )
        
        stats = pa.stats
        assert stats["total_files"] == 1
        assert stats["total_classes"] == 2
        assert stats["total_functions"] == 1

    def test_project_to_dict(self):
        """Vérifie la conversion en dict."""
        pa = ProjectAnalysis(project_name="test")
        result = pa.to_dict()
        
        assert isinstance(result, dict)
        assert result["project_name"] == "test"
        assert "stats" in result


class TestRelation:
    """Tests pour Relation."""

    def test_create_import_relation(self):
        """Crée une relation d'import."""
        rel = Relation(
            from_entity="main.py",
            from_file="main.py",
            to_entity="User",
            to_file="models.py",
            type="import"
        )
        assert rel.type == "import"
        assert rel.to_entity == "User"

    def test_create_inheritance_relation(self):
        """Crée une relation d'héritage."""
        rel = Relation(
            from_entity="AdminUser",
            from_file="models.py",
            to_entity="User",
            to_file="models.py",
            type="inheritance"
        )
        assert rel.type == "inheritance"
        assert rel.from_entity == "AdminUser"
