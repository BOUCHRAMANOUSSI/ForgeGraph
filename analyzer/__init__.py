"""
ForgeGraph — Module Analyse & Ingestion

Point d'entrée principal : analyze_project()

Exemple d'utilisation :
    from analyzer import analyze_project
    result = analyze_project("/path/to/project")
    print(f"Trouvé {result['stats']['total_classes']} classes")
"""

from analyzer.analyzer import analyze_project
from analyzer.scanner import scan_project, get_project_name
from analyzer.parser_python import parse_python_file
from analyzer.relations import extract_relations
from analyzer.entities import (
    ProjectAnalysis,
    FileAnalysis,
    ClassEntity,
    FunctionEntity,
    ImportEntity,
    GlobalVariable,
    Relation,
    FunctionArg,
)

__all__ = [
    "analyze_project",
    "scan_project",
    "parse_python_file",
    "extract_relations",
    "get_project_name",
    "ProjectAnalysis",
    "FileAnalysis",
    "ClassEntity",
    "FunctionEntity",
    "ImportEntity",
    "GlobalVariable",
    "Relation",
    "FunctionArg",
]
