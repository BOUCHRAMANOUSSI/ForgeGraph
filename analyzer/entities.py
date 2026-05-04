"""
entities.py — Modèles de données pour les entités extraites du code source.

Ce module définit les dataclasses qui représentent la structure d'un projet :
- FunctionArg   : un argument d'une fonction
- FunctionEntity : une fonction ou méthode
- ClassEntity    : une classe avec ses méthodes
- ImportEntity   : un import (import X ou from X import Y)
- GlobalVariable : une variable/constante de module
- FileAnalysis   : l'analyse complète d'un fichier
- ProjectAnalysis : l'analyse complète d'un projet

Auteur : Bouchra
Date   : 2026-04-24
"""

from __future__ import annotations

from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from typing import Any


# ─────────────────────────────────────────────
# Argument d'une fonction
# ─────────────────────────────────────────────
@dataclass
class FunctionArg:
    """Représente un argument d'une fonction ou méthode."""
    name: str
    type: str | None = None
    default: str | None = None


# ─────────────────────────────────────────────
# Fonction / Méthode
# ─────────────────────────────────────────────
@dataclass
class FunctionEntity:
    """
    Représente une fonction Python (top-level ou méthode d'une classe).
    
    Attributs :
        name        : Nom de la fonction (ex: "create_user")
        args        : Liste des arguments avec leurs types
        return_type : Type de retour annoté (ex: "str", "list[int]")
        is_async    : True si c'est une fonction async
        decorators  : Liste des noms de décorateurs (ex: ["staticmethod"])
        docstring   : Première ligne de la docstring, ou None
        line_start  : Numéro de la première ligne dans le fichier
        line_end    : Numéro de la dernière ligne dans le fichier
    """
    name: str
    args: list[FunctionArg] = field(default_factory=list)
    return_type: str | None = None
    is_async: bool = False
    decorators: list[str] = field(default_factory=list)
    docstring: str | None = None
    line_start: int = 0
    line_end: int = 0


# ─────────────────────────────────────────────
# Classe
# ─────────────────────────────────────────────
@dataclass
class ClassEntity:
    """
    Représente une classe Python.
    
    Attributs :
        name         : Nom de la classe (ex: "VectorStoreService")
        methods      : Liste des méthodes de la classe
        base_classes : Classes parentes (ex: ["BaseService", "Mixin"])
        decorators   : Décorateurs de la classe (ex: ["dataclass"])
        docstring    : Docstring de la classe
        line_start   : Première ligne
        line_end     : Dernière ligne
    """
    name: str
    methods: list[FunctionEntity] = field(default_factory=list)
    base_classes: list[str] = field(default_factory=list)
    decorators: list[str] = field(default_factory=list)
    docstring: str | None = None
    line_start: int = 0
    line_end: int = 0


# ─────────────────────────────────────────────
# Import
# ─────────────────────────────────────────────
@dataclass
class ImportEntity:
    """
    Représente un import Python.
    
    Exemples :
        import logging          → type="import", module="logging", names=[]
        from os.path import join → type="from", module="os.path", names=["join"]
    """
    type: str  # "import" ou "from"
    module: str
    names: list[str] = field(default_factory=list)
    line: int = 0


# ─────────────────────────────────────────────
# Variable globale / Constante
# ─────────────────────────────────────────────
@dataclass
class GlobalVariable:
    """
    Représente une variable définie au niveau du module.
    
    Exemples :
        MAX_RETRIES = 3
        _DEFAULT_MODEL = "ollama/phi3"
    """
    name: str
    value: str | None = None
    line: int = 0


# ─────────────────────────────────────────────
# Relation entre entités
# ─────────────────────────────────────────────
@dataclass
class Relation:
    """
    Représente une relation entre deux entités du projet.
    
    Types supportés :
        - "import"      : Un fichier importe une entité d'un autre
        - "inheritance"  : Une classe hérite d'une autre
        - "call"         : Une fonction appelle une autre (Sprint 2)
    """
    from_entity: str
    from_file: str
    to_entity: str
    to_file: str | None = None  # None si on ne peut pas résoudre le fichier cible
    type: str = "import"  # "import", "inheritance", "call"


# ─────────────────────────────────────────────
# Analyse d'un fichier
# ─────────────────────────────────────────────
@dataclass
class FileAnalysis:
    """Résultat de l'analyse d'un seul fichier Python."""
    path: str
    size_bytes: int = 0
    total_lines: int = 0
    classes: list[ClassEntity] = field(default_factory=list)
    functions: list[FunctionEntity] = field(default_factory=list)
    imports: list[ImportEntity] = field(default_factory=list)
    global_variables: list[GlobalVariable] = field(default_factory=list)
    error: str | None = None  # Message d'erreur si le parsing a échoué


# ─────────────────────────────────────────────
# Analyse complète du projet
# ─────────────────────────────────────────────
@dataclass
class ProjectAnalysis:
    """
    Résultat complet de l'analyse d'un projet.
    C'est l'objet racine qui sera sérialisé en JSON.
    """
    project_name: str
    language: str = "python"
    analyzed_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    files: list[FileAnalysis] = field(default_factory=list)
    relations: list[Relation] = field(default_factory=list)

    @property
    def stats(self) -> dict[str, int]:
        """Calcule les statistiques globales du projet."""
        return {
            "total_files": len(self.files),
            "total_classes": sum(len(f.classes) for f in self.files),
            "total_functions": sum(len(f.functions) for f in self.files),
            "total_methods": sum(
                sum(len(c.methods) for c in f.classes)
                for f in self.files
            ),
            "total_imports": sum(len(f.imports) for f in self.files),
            "files_with_errors": sum(1 for f in self.files if f.error is not None),
        }

    def to_dict(self) -> dict[str, Any]:
        """Convertit l'analyse complète en dictionnaire JSON-compatible."""
        result = asdict(self)
        # Remplacer le champ stats calculé dynamiquement
        result["stats"] = self.stats
        return result
