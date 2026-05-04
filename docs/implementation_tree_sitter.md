# 🌳 Documentation : Implémentation du Parsing avec Tree-sitter

> **Projet** : ForgeGraph  
> **Module** : Analyse & Ingestion  
> **Auteur** : Bouchra  
> **Date** : 2026-04-24  

---

## 1. Pourquoi Tree-sitter ?

Conformément aux exigences du Sprint 1, le module d'analyse utilise **Tree-sitter** pour parser le code source au lieu du module Python natif `ast`.

**Avantages majeurs de Tree-sitter :**
- **Multi-langage** : Le même moteur peut parser du Python, JavaScript, Java, Go, C++, etc. Cela prépare le terrain pour les futurs sprints de ForgeGraph.
- **Incrémentiel et Rapide** : Écrit en C, il est extrêmement performant.
- **Robuste aux erreurs** : Contrairement à `ast` qui plante (SyntaxError) si le code est malformé, Tree-sitter est capable de parser partiellement un fichier contenant des erreurs et de construire un arbre pour le reste du code valide.

## 2. Installation et Configuration

Pour utiliser Tree-sitter en Python, deux paquets ont été installés :
```bash
pip install tree-sitter tree-sitter-python
```

- `tree-sitter` : Le moteur principal en Python.
- `tree-sitter-python` : La grammaire spécifique au langage Python.

## 3. Fonctionnement du Parser (`parser_python.py`)

Le cœur du parsing se trouve dans la fonction `parse_python_file(file_path)` :

1. **Lecture du fichier** : Le code source est lu et encodé en octets (bytes), car Tree-sitter requiert des bytes pour fonctionner.
2. **Initialisation** : 
   ```python
   import tree_sitter_python as tspython
   from tree_sitter import Language, Parser

   PY_LANGUAGE = Language(tspython.language())
   parser = Parser(PY_LANGUAGE)
   ```
3. **Génération de l'arbre CST (Concrete Syntax Tree)** :
   ```python
   tree = parser.parse(bytes(source_code, "utf-8"))
   root = tree.root_node
   ```
4. **Parcours des nœuds** : Le script itère sur `root.children` pour identifier les entités principales.

## 4. Correspondance des Nœuds Tree-sitter

Voici comment les concepts Python sont traduits en types de nœuds Tree-sitter dans notre implémentation :

| Élément Python | Type de Nœud Tree-sitter | Entité ForgeGraph générée |
|----------------|--------------------------|---------------------------|
| Classe | `class_definition` | `ClassEntity` |
| Fonction / Méthode | `function_definition` | `FunctionEntity` |
| Élément avec décorateur | `decorated_definition` | `ClassEntity` ou `FunctionEntity` |
| Importation (`import x`) | `import_statement` | `ImportEntity` |
| Importation (`from x import y`) | `import_from_statement` | `ImportEntity` |
| Assignation (`x = 1`) | `assignment` (dans `expression_statement`) | `GlobalVariable` |
| Docstring | `string` (premier nœud d'un `block`) | `docstring` (attribut) |
| Décorateur | `decorator` | `decorators` (attribut liste) |

## 5. Défis techniques résolus

L'utilisation de Tree-sitter nécessite une manipulation bas niveau de l'arbre syntaxique, ce qui a demandé de résoudre plusieurs défis techniques :

### A. Extraction du texte source
Les nœuds Tree-sitter ne contiennent pas directement le texte, mais des coordonnées. Une fonction utilitaire a été créée pour décoder les octets du nœud :
```python
def _node_text(node: Node) -> str:
    return node.text.decode("utf-8")
```

### B. Gestion des Décorateurs
Tree-sitter encapsule souvent une classe ou fonction décorée dans un nœud parent `decorated_definition`. Le script doit d'abord identifier ce nœud parent, extraire la liste des enfants de type `decorator`, puis trouver la définition réelle (`class_definition` ou `function_definition`) imbriquée à l'intérieur.

### C. Gestion complexe des arguments de fonctions
L'extraction des arguments (`parameters`) a dû prendre en compte 6 cas distincts :
1. `identifier` : Argument simple (ex: `self`)
2. `typed_parameter` : Argument avec type (ex: `name: str`)
3. `default_parameter` : Argument avec valeur par défaut (ex: `salt="default"`)
4. `typed_default_parameter` : Argument typé avec défaut (ex: `max_tokens: int = 8000`)
5. `list_splat_pattern` : Arguments variables (`*args`)
6. `dictionary_splat_pattern` : Arguments mots-clés variables (`**kwargs`)

### D. Tolérance aux erreurs de syntaxe
Si le fichier contient une erreur (ex: parenthèse manquante), Tree-sitter génère un nœud de type `ERROR` mais continue de parser le reste. Notre implémentation détecte la propriété `root.has_error`, signale la ligne problématique dans les logs, mais retourne quand même toutes les classes et fonctions valides qu'il a pu trouver.

## 6. Structure des données extraites

Le résultat du parsing est standardisé selon l'interface définie au Jour 2 :

```json
{
  "classes": [...],
  "functions": [...],
  "imports": [...],
  "global_variables": [...],
  "error": "Message d'erreur s'il y a un problème de syntaxe critique"
}
```

Ce format JSON est prêt à être consommé par le module d'Orchestration & IA géré par Mimoun.
