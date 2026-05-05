# 🔬 Recherche — Outils de Parsing & Entités à Extraire

## 1. Types d'entités à extraire

| Entité | Description | 
|--------|-------------|
| **Classe** | Nom, méthodes, classes parentes, décorateurs |
| **Fonction** | Nom, arguments, type de retour, async ou non | 
| **Méthode** | Fonction à l'intérieur d'une classe | 
| **Import** | Modules importés, noms spécifiques | 
| **Variable globale** | Constantes et variables de module | 
| **Décorateur** | @staticmethod, @property, @router.get... |

## 2. Types de relations entre entités

| Relation | Exemple | 
|----------|---------|
| **Héritage** | `class Dog(Animal)` → Dog hérite de Animal |
| **Import** | `from app.models import User` → le fichier utilise User | 
| **Appel de fonction** | `result = hash_password(pwd)` → appelle hash_password | 
| **Composition** | Classe A contient un attribut de type Classe B | 

## 3. Outils de parsing étudiés

### 3.1 Module `ast` (Python built-in) ✅ CHOIX RETENU

- **Avantages** :
  - Intégré à Python, aucune dépendance externe
  - API simple et bien documentée
  - Parfait pour parser du code Python
  - Donne accès aux numéros de lignes
  - Supporte Python 3.8+ avec les annotations de type
- **Inconvénients** :
  - Ne supporte QUE Python
  - Ne peut pas parser du code avec des erreurs de syntaxe
- **Nœuds AST importants** :
  - `ast.ClassDef` → Définition de classe
  - `ast.FunctionDef` / `ast.AsyncFunctionDef` → Fonctions
  - `ast.Import` / `ast.ImportFrom` → Imports
  - `ast.Assign` → Variables
  - `ast.Call` → Appels de fonction

### 3.2 `tree-sitter` (Multi-langage)

- **Avantages** :
  - Supporte 100+ langages (Python, JS, Java, Go, Rust...)
  - Très performant (écrit en C)
  - Peut parser du code avec des erreurs de syntaxe
- **Inconvénients** :
  - Nécessite une installation plus complexe (bindings C)
  - API moins intuitive que `ast`
- **Verdict** : À envisager pour le Sprint 2 si on veut supporter d'autres langages

### 3.3 `esprima` / `acorn` (JavaScript)

- **Avantages** : Spécialisé JavaScript/TypeScript
- **Inconvénients** : Ne supporte que JS
- **Verdict** : Utile uniquement si on ajoute le support JavaScript

## 4. Décision finale Sprint 1

> **On commence par Python uniquement avec le module `ast`.**
> C'est le plus simple, le plus fiable, et ça couvre notre besoin immédiat
> (analyser des projets Python comme ChatNow).
> Le support multi-langage (via tree-sitter) sera ajouté dans un sprint futur.

## 5. Exemples d'utilisation de `ast`

```python
import ast

# Parser un fichier Python
with open("example.py") as f:
    tree = ast.parse(f.read())

# Parcourir les nœuds de premier niveau
for node in ast.iter_child_nodes(tree):
    if isinstance(node, ast.ClassDef):
        print(f"Classe trouvée : {node.name} (ligne {node.lineno})")
    elif isinstance(node, ast.FunctionDef):
        print(f"Fonction trouvée : {node.name} (ligne {node.lineno})")
```
