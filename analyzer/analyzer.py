"""
analyzer.py — Point d'entrée principal du module d'analyse.

Orchestre le scanning et le parsing pour fournir une analyse complète du projet.

Auteur : Bouchra
Date   : 2026-04-24
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

from analyzer.scanner import scan_project, get_project_name
from analyzer.parser_python import parse_python_file
from analyzer.relations import extract_relations
from analyzer.entities import ProjectAnalysis, FileAnalysis

logger = logging.getLogger(__name__)


def analyze_project(project_path: str, language: str = "python") -> dict[str, Any]:
    """
    Analyse complète d'un projet et retourne les résultats en JSON.
    
    Point d'entrée principal du module Analyse & Ingestion.
    Orchestre le scanning, le parsing et l'extraction des relations.
    
    Args:
        project_path : Chemin absolu vers le dossier racine du projet.
                       Fourni par le module Infrastructure (Abdelhakim).
        language     : Langage cible ("python" pour Sprint 1).
    
    Returns:
        Dictionnaire JSON-compatible contenant :
        - project_name : Nom du projet (extrait du chemin)
        - language     : Langage analysé
        - analyzed_at  : Timestamp ISO 8601 de l'analyse
        - stats        : Statistiques globales
        - files        : Liste des analyses de fichiers
        - relations    : Liste des relations détectées
    
    Raises:
        FileNotFoundError : Si le dossier project_path n'existe pas
        ValueError        : Si le langage n'est pas supporté
        
    Example:
        >>> result = analyze_project("/path/to/my/project")
        >>> print(result["stats"]["total_classes"])
        12
        >>> json.dump(result, open("output.json", "w"))
    """
    
    # Valider que le dossier existe
    root_path = Path(project_path).resolve()
    if not root_path.exists():
        raise FileNotFoundError(f"Le dossier '{project_path}' n'existe pas.")
    if not root_path.is_dir():
        raise NotADirectoryError(f"'{project_path}' n'est pas un dossier.")
    
    logger.info(f"Début de l'analyse du projet : {root_path}")
    
    # ── Étape 1 : Scan récursif des fichiers source ──
    try:
        found_files = scan_project(
            str(root_path),
            language=language,
            include_init=True,
            include_tests=False,
        )
        logger.info(f"Scan terminé : {len(found_files)} fichiers trouvés")
    except ValueError as e:
        logger.error(f"Erreur de langage : {e}")
        raise
    
    # ── Étape 2 : Parsing de chaque fichier ──
    file_analyses: list[FileAnalysis] = []
    parse_errors = 0
    
    for file_info in found_files:
        abs_path = file_info["abs_path"]
        rel_path = file_info["path"]
        
        try:
            if language == "python":
                analysis = parse_python_file(abs_path)
                # Stocker le chemin relatif pour la sortie
                analysis.path = rel_path
                file_analyses.append(analysis)
                
                if analysis.error:
                    parse_errors += 1
                    logger.warning(f"Erreur dans {rel_path}: {analysis.error}")
            else:
                logger.warning(f"Langage '{language}' non implémenté (Sprint 2+)")
        
        except Exception as e:
            logger.error(f"Exception lors du parsing de {rel_path}: {e}")
            parse_errors += 1
    
    logger.info(f"Parsing terminé : {len(file_analyses)} fichiers analysés, {parse_errors} erreurs")
    
    # ── Étape 3 : Extraction des relations ──
    try:
        relations = extract_relations(file_analyses)
        logger.info(f"Relations extraites : {len(relations)} dépendances détectées")
    except Exception as e:
        logger.error(f"Erreur lors de l'extraction des relations: {e}")
        relations = []
    
    # ── Étape 4 : Construire l'objet ProjectAnalysis ──
    project_name = get_project_name(str(root_path))
    
    analysis = ProjectAnalysis(
        project_name=project_name,
        language=language,
        files=file_analyses,
        relations=relations,
    )
    
    # ── Étape 5 : Sérialiser en JSON ──
    result = analysis.to_dict()
    
    logger.info(f"Analyse complète du projet '{project_name}' terminée.")
    logger.info(f"  - Fichiers: {result['stats']['total_files']}")
    logger.info(f"  - Classes: {result['stats']['total_classes']}")
    logger.info(f"  - Fonctions: {result['stats']['total_functions']}")
    logger.info(f"  - Imports: {result['stats']['total_imports']}")
    logger.info(f"  - Relations: {len(relations)}")
    
    return result
