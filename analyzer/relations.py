"""
relations.py — Extraction des relations entre entités.

Extrait les dépendances (imports, héritage) entre les entités du projet.

Types de relations supportés :
- import     : Fichier A importe une entité de Fichier B
- inheritance : Classe A hérite de Classe B

Note : La détection des appels de fonction est planifiée pour Sprint 2.

Auteur : Bouchra
Date   : 2026-04-24
"""

from __future__ import annotations

import logging
from analyzer.entities import FileAnalysis, Relation

logger = logging.getLogger(__name__)


def extract_relations(files: list[FileAnalysis]) -> list[Relation]:
    """
    Extrait les relations entre les entités de tous les fichiers analysés.
    
    Types de relations détectées :
    - import     : Un module importe une entité d'un autre module
    - inheritance : Une classe hérite d'une autre classe
    
    Args:
        files : Liste des FileAnalysis produits par le parser.
    
    Returns:
        Liste de Relations détectées.
    """
    relations: list[Relation] = []

    # Construire deux index :
    # 1. classes par nom simple pour résoudre les héritages
    # 2. classes par (module, nom) pour résoudre les imports
    class_by_name: dict[str, str] = {}  # nom_classe → chemin_fichier
    class_by_module: dict[tuple[str, str], str] = {}  # (module_alias, nom_classe) → chemin_fichier
    function_by_name: dict[str, str] = {}  # nom_fonction → chemin_fichier
    
    for file_analysis in files:
        # Index les classes
        for cls in file_analysis.classes:
            class_by_name[cls.name] = file_analysis.path
        
        # Index les fonctions
        for func in file_analysis.functions:
            function_by_name[func.name] = file_analysis.path

    # Extraire les relations
    for file_analysis in files:
        # ── Relations d'import ──
        for imp in file_analysis.imports:
            if imp.type == "from":
                # from X import Y, Z
                for name in imp.names:
                    # Chercher si Y ou Z est une classe connue
                    if name in class_by_name:
                        relations.append(Relation(
                            from_entity=file_analysis.path,
                            from_file=file_analysis.path,
                            to_entity=name,
                            to_file=class_by_name[name],
                            type="import",
                        ))
                    elif name in function_by_name:
                        relations.append(Relation(
                            from_entity=file_analysis.path,
                            from_file=file_analysis.path,
                            to_entity=name,
                            to_file=function_by_name[name],
                            type="import",
                        ))
            else:
                # import X → chercher si X est un module connu (future feature)
                # Pour Sprint 1, on ignore les imports simples
                pass

        # ── Relations d'héritage ──
        for cls in file_analysis.classes:
            for base in cls.base_classes:
                # Résoudre le nom de la classe parente
                base_name = base.split(".")[-1]  # Ex: "app.models.Base" → "Base"
                
                if base_name in class_by_name:
                    target_file = class_by_name[base_name]
                    relations.append(Relation(
                        from_entity=cls.name,
                        from_file=file_analysis.path,
                        to_entity=base_name,
                        to_file=target_file,
                        type="inheritance",
                    ))
                else:
                    # La classe parente n'a pas été trouvée dans le projet
                    # (peut-être une classe importée d'une bibliothèque externe)
                    logger.debug(f"Classe parente '{base_name}' non trouvée pour {cls.name}")

    return relations
