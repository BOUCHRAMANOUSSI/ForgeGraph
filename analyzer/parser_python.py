"""
parser_python.py — Parseur de fichiers Python via Tree-sitter.

Ce module analyse un fichier Python en utilisant tree-sitter et en extrait :
- Les classes (avec leurs méthodes)
- Les fonctions top-level
- Les imports
- Les variables globales

Tree-sitter est un parseur incrémental multi-langage, écrit en C,
qui produit un arbre syntaxique concret (CST) à partir du code source.

Auteur : Bouchra
Date   : 2026-04-24
"""

from __future__ import annotations

import logging
from pathlib import Path

import tree_sitter_python as tspython
from tree_sitter import Language, Parser, Node

from analyzer.entities import (
    ClassEntity,
    FileAnalysis,
    FunctionArg,
    FunctionEntity,
    GlobalVariable,
    ImportEntity,
)

logger = logging.getLogger(__name__)

# ─────────────────────────────────────────────
# Initialisation de Tree-sitter pour Python
# ─────────────────────────────────────────────
PY_LANGUAGE = Language(tspython.language())
_parser = Parser(PY_LANGUAGE)


# ─────────────────────────────────────────────
# Utilitaires Tree-sitter
# ─────────────────────────────────────────────

def _node_text(node: Node) -> str:
    """Extrait le texte source d'un nœud tree-sitter."""
    return node.text.decode("utf-8")


def _find_children_by_type(node: Node, type_name: str) -> list[Node]:
    """Trouve tous les enfants directs d'un type donné."""
    return [child for child in node.children if child.type == type_name]


def _find_child_by_type(node: Node, type_name: str) -> Node | None:
    """Trouve le premier enfant direct d'un type donné."""
    for child in node.children:
        if child.type == type_name:
            return child
    return None


def _find_child_by_field(node: Node, field_name: str) -> Node | None:
    """Trouve un enfant par nom de champ (field name)."""
    return node.child_by_field_name(field_name)


# ─────────────────────────────────────────────
# Extraction des décorateurs
# ─────────────────────────────────────────────

def _extract_decorators(node: Node) -> list[str]:
    """Extrait les noms des décorateurs d'une classe ou fonction."""
    decorators: list[str] = []
    for child in node.children:
        if child.type == "decorator":
            # Le décorateur contient '@' suivi du nom/expression
            # On prend tout sauf le '@'
            dec_text = _node_text(child).lstrip("@").strip()
            # Pour @dataclass(frozen=True), on garde juste "dataclass"
            if "(" in dec_text:
                dec_text = dec_text.split("(")[0]
            decorators.append(dec_text)
    return decorators


# ─────────────────────────────────────────────
# Extraction de la docstring
# ─────────────────────────────────────────────

def _extract_docstring(node: Node) -> str | None:
    """Extrait la docstring d'une classe ou fonction."""
    # La docstring est le premier statement du body qui est un expression_statement
    # contenant un string
    body = _find_child_by_type(node, "block")
    if body is None:
        return None

    for child in body.children:
        if child.type == "expression_statement":
            string_node = _find_child_by_type(child, "string")
            if string_node:
                raw = _node_text(string_node)
                # Nettoyer les guillemets triples
                cleaned = raw.strip("\"'").strip()
                # Garder seulement la première ligne
                first_line = cleaned.split("\n")[0].strip()
                if len(first_line) > 200:
                    return first_line[:200] + "..."
                return first_line if first_line else None
            break
        # Si le premier statement n'est pas une docstring, on arrête
        if child.type not in ("comment", "newline"):
            break

    return None


# ─────────────────────────────────────────────
# Extraction du type de retour
# ─────────────────────────────────────────────

def _extract_return_type(node: Node) -> str | None:
    """Extrait le type de retour d'une fonction."""
    ret = _find_child_by_field(node, "return_type")
    if ret is not None:
        return _node_text(ret)
    return None


# ─────────────────────────────────────────────
# Extraction des arguments d'une fonction
# ─────────────────────────────────────────────

def _extract_args(node: Node) -> list[FunctionArg]:
    """Extrait les arguments d'une fonction tree-sitter."""
    args: list[FunctionArg] = []

    params_node = _find_child_by_field(node, "parameters")
    if params_node is None:
        return args

    for child in params_node.children:
        if child.type == "identifier":
            # Argument simple (ex: self, x)
            args.append(FunctionArg(name=_node_text(child)))

        elif child.type == "typed_parameter":
            # Argument typé (ex: name: str)
            name_node = child.children[0] if child.children else None
            name = _node_text(name_node) if name_node else "?"
            # Le type est après le ":"
            type_node = _find_child_by_type(child, "type")
            arg_type = _node_text(type_node) if type_node else None
            args.append(FunctionArg(name=name, type=arg_type))

        elif child.type == "default_parameter":
            # Argument avec valeur par défaut (ex: salt="default")
            name_node = _find_child_by_field(child, "name")
            value_node = _find_child_by_field(child, "value")
            name = _node_text(name_node) if name_node else "?"
            default = _node_text(value_node) if value_node else None
            args.append(FunctionArg(name=name, default=default))

        elif child.type == "typed_default_parameter":
            # Argument typé avec défaut (ex: max_tokens: int = 8000)
            name_node = _find_child_by_field(child, "name")
            type_node = _find_child_by_type(child, "type")
            value_node = _find_child_by_field(child, "value")
            name = _node_text(name_node) if name_node else "?"
            arg_type = _node_text(type_node) if type_node else None
            default = _node_text(value_node) if value_node else None
            args.append(FunctionArg(name=name, type=arg_type, default=default))

        elif child.type == "list_splat_pattern":
            # *args
            name_node = child.children[0] if child.children else None
            name = _node_text(name_node) if name_node else "args"
            args.append(FunctionArg(name=f"*{name}"))

        elif child.type == "dictionary_splat_pattern":
            # **kwargs
            name_node = child.children[0] if child.children else None
            name = _node_text(name_node) if name_node else "kwargs"
            args.append(FunctionArg(name=f"**{name}"))

    return args


# ─────────────────────────────────────────────
# Extraction d'une fonction / méthode
# ─────────────────────────────────────────────

def _extract_function(node: Node) -> FunctionEntity:
    """Extrait les informations d'une fonction ou méthode depuis un nœud tree-sitter."""
    name_node = _find_child_by_field(node, "name")
    name = _node_text(name_node) if name_node else "unknown"

    # Détecter si c'est async : chercher keyword "async" parmi les enfants
    is_async = any(
        child.type == "async" or _node_text(child) == "async"
        for child in node.children
    )

    return FunctionEntity(
        name=name,
        args=_extract_args(node),
        return_type=_extract_return_type(node),
        is_async=is_async,
        decorators=_extract_decorators(node),
        docstring=_extract_docstring(node),
        line_start=node.start_point[0] + 1,  # tree-sitter est 0-indexed
        line_end=node.end_point[0] + 1,
    )


# ─────────────────────────────────────────────
# Extraction d'une classe
# ─────────────────────────────────────────────

def _extract_class(node: Node) -> ClassEntity:
    """Extrait les informations d'une classe depuis un nœud tree-sitter."""
    name_node = _find_child_by_field(node, "name")
    name = _node_text(name_node) if name_node else "unknown"

    # Classes parentes (superclass_list ou argument_list)
    base_classes: list[str] = []
    superclass = _find_child_by_field(node, "superclasses")
    if superclass:
        for child in superclass.children:
            if child.type == "identifier":
                base_classes.append(_node_text(child))
            elif child.type == "attribute":
                base_classes.append(_node_text(child))
            elif child.type == "keyword_argument":
                pass  # metaclass=... etc, on ignore

    # Décorateurs
    decorators = _extract_decorators(node)

    # Méthodes (function_definition à l'intérieur du body)
    methods: list[FunctionEntity] = []
    body = _find_child_by_type(node, "block")
    if body:
        for child in body.children:
            if child.type in ("function_definition", "decorated_definition"):
                if child.type == "decorated_definition":
                    # Trouver la vraie function_definition dans la decorated_definition
                    func_node = _find_child_by_type(child, "function_definition")
                    if func_node:
                        method = _extract_function(func_node)
                        # Ajouter les décorateurs du decorated_definition
                        method.decorators = _extract_decorators(child)
                        # Vérifier async au niveau du decorated_definition
                        if any(_node_text(c) == "async" for c in child.children):
                            method.is_async = True
                        methods.append(method)
                else:
                    methods.append(_extract_function(child))

    return ClassEntity(
        name=name,
        methods=methods,
        base_classes=base_classes,
        decorators=decorators,
        docstring=_extract_docstring(node),
        line_start=node.start_point[0] + 1,
        line_end=node.end_point[0] + 1,
    )


# ─────────────────────────────────────────────
# Extraction des imports
# ─────────────────────────────────────────────

def _extract_imports(root: Node) -> list[ImportEntity]:
    """Extrait tous les imports du module."""
    imports: list[ImportEntity] = []

    for child in root.children:
        if child.type == "import_statement":
            # import X, import X as Y
            for name_child in child.children:
                if name_child.type == "dotted_name":
                    imports.append(ImportEntity(
                        type="import",
                        module=_node_text(name_child),
                        names=[],
                        line=child.start_point[0] + 1,
                    ))
                elif name_child.type == "aliased_import":
                    dotted = _find_child_by_type(name_child, "dotted_name")
                    if dotted:
                        imports.append(ImportEntity(
                            type="import",
                            module=_node_text(dotted),
                            names=[],
                            line=child.start_point[0] + 1,
                        ))
                elif name_child.type == "identifier" and _node_text(name_child) not in ("import", "as"):
                    # Import simple : import X
                    imports.append(ImportEntity(
                        type="import",
                        module=_node_text(name_child),
                        names=[],
                        line=child.start_point[0] + 1,
                    ))

        elif child.type == "import_from_statement":
            # from X import Y, Z
            module_node = _find_child_by_field(child, "module_name")
            module = _node_text(module_node) if module_node else ""

            names: list[str] = []
            for sub in child.children:
                if sub.type == "dotted_name" and sub != module_node:
                    names.append(_node_text(sub))
                elif sub.type == "aliased_import":
                    dotted = _find_child_by_type(sub, "dotted_name")
                    if dotted:
                        names.append(_node_text(dotted))
                    else:
                        # Peut être juste un identifier
                        for node in sub.children:
                            if node.type == "identifier":
                                names.append(_node_text(node))
                                break
                elif sub.type == "identifier" and _node_text(sub) not in ("from", "import", "as", ",", "(", ")"):
                    names.append(_node_text(sub))

            # Si pas de module_node, chercher autrement
            if not module:
                for sub in child.children:
                    if sub.type == "dotted_name":
                        module = _node_text(sub)
                        if module in names:
                            names.remove(module)
                        break
                    elif sub.type == "relative_import":
                        module = _node_text(sub)
                        break

            if module or names:  # Ajouter seulement si on a au moins le module ou les noms
                imports.append(ImportEntity(
                    type="from",
                    module=module,
                    names=names,
                    line=child.start_point[0] + 1,
                ))

    return imports


# ─────────────────────────────────────────────
# Extraction des variables globales
# ─────────────────────────────────────────────

def _extract_global_variables(root: Node) -> list[GlobalVariable]:
    """Extrait les variables définies au niveau du module."""
    variables: list[GlobalVariable] = []

    for child in root.children:
        if child.type == "expression_statement":
            # Chercher les assignments dans les expression_statements
            assign = _find_child_by_type(child, "assignment")
            if assign:
                left = _find_child_by_field(assign, "left")
                right = _find_child_by_field(assign, "right")
                if left and left.type == "identifier":
                    value_str = _node_text(right) if right else None
                    if value_str and len(value_str) > 100:
                        value_str = value_str[:100] + "..."
                    variables.append(GlobalVariable(
                        name=_node_text(left),
                        value=value_str,
                        line=child.start_point[0] + 1,
                    ))

    return variables


# ─────────────────────────────────────────────
# Fonction principale : analyser un fichier
# ─────────────────────────────────────────────

def parse_python_file(file_path: str) -> FileAnalysis:
    """
    Analyse un fichier Python avec Tree-sitter et retourne un objet FileAnalysis.

    Tree-sitter produit un arbre syntaxique concret (CST) qui est ensuite
    parcouru pour extraire les classes, fonctions, imports et variables.

    Args:
        file_path : Chemin absolu vers le fichier .py à analyser.

    Returns:
        FileAnalysis contenant les classes, fonctions, imports et variables.
        Si le fichier a une erreur, FileAnalysis.error contiendra le message.
    """
    path = Path(file_path)

    # Informations de base
    try:
        size_bytes = path.stat().st_size
    except OSError:
        size_bytes = 0

    # Lire le contenu du fichier
    try:
        source_code = path.read_text(encoding="utf-8")
    except FileNotFoundError:
        return FileAnalysis(
            path=file_path,
            size_bytes=0,
            error=f"Fichier introuvable : {file_path}",
        )
    except UnicodeDecodeError:
        try:
            source_code = path.read_text(encoding="latin-1")
            logger.warning(f"Fichier '{file_path}' lu en latin-1 (pas UTF-8).")
        except Exception as e:
            return FileAnalysis(
                path=file_path,
                size_bytes=size_bytes,
                error=f"Erreur de lecture : {e}",
            )

    total_lines = source_code.count("\n") + 1

    # Parser avec Tree-sitter
    source_bytes = bytes(source_code, "utf-8")
    tree = _parser.parse(source_bytes)
    root = tree.root_node

    # Vérifier les erreurs de syntaxe dans l'arbre
    has_error = root.has_error
    if has_error:
        # Tree-sitter peut quand même parser partiellement le fichier
        # On signale l'erreur mais on continue l'extraction
        error_nodes = [n for n in _walk_tree(root) if n.type == "ERROR"]
        error_lines = [n.start_point[0] + 1 for n in error_nodes[:3]]
        error_msg = f"SyntaxError lignes {error_lines}"
        logger.warning(f"Erreurs de syntaxe dans '{file_path}' : {error_msg}")
    else:
        error_msg = None

    # Extraire les entités de premier niveau
    classes: list[ClassEntity] = []
    functions: list[FunctionEntity] = []

    for child in root.children:
        if child.type == "class_definition":
            classes.append(_extract_class(child))
        elif child.type == "function_definition":
            functions.append(_extract_function(child))
        elif child.type == "decorated_definition":
            # Classe ou fonction décorée
            inner = _find_child_by_type(child, "class_definition")
            if inner:
                cls = _extract_class(inner)
                cls.decorators = _extract_decorators(child)
                classes.append(cls)
            else:
                inner = _find_child_by_type(child, "function_definition")
                if inner:
                    func = _extract_function(inner)
                    func.decorators = _extract_decorators(child)
                    # Vérifier si c'est async au niveau du decorated_definition
                    if any(_node_text(c) == "async" for c in child.children):
                        func.is_async = True
                    functions.append(func)

    # Imports
    imports = _extract_imports(root)

    # Variables globales
    global_variables = _extract_global_variables(root)

    logger.info(
        f"[tree-sitter] Parsé '{path.name}' : "
        f"{len(classes)} classes, {len(functions)} fonctions, "
        f"{len(imports)} imports, {len(global_variables)} variables"
    )

    return FileAnalysis(
        path=file_path,
        size_bytes=size_bytes,
        total_lines=total_lines,
        classes=classes,
        functions=functions,
        imports=imports,
        global_variables=global_variables,
        error=error_msg,
    )


def _walk_tree(node: Node):
    """Parcourt récursivement tous les nœuds de l'arbre tree-sitter."""
    yield node
    for child in node.children:
        yield from _walk_tree(child)
