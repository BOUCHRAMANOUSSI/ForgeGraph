# 📋 Implémentation du Module Analyse & Ingestion

> **Auteur** : Bouchra  
> **Date** : 2026-04-24  
> **Sprint** : Sprint 1

---

## 1. Vue d'ensemble de l'implémentation

Le module **Analyse & Ingestion** est structuré en 5 composants :

```
┌─────────────────────────────────────────────────────────────┐
│                   analyze_project()                         │ (analyzer.py)
│                   Point d'entrée unique                     │
└───────┬──────────────────┬──────────────────┬───────────────┘
        ↓                  ↓                  ↓
    ┌────────┐      ┌────────────┐     ┌───────────────┐
    │ Scanner│      │   Parser   │     │  Relations    │
    │(Phase1)│      │  (Phase 2) │     │  (Phase 3)    │
    └────────┘      └────────────┘     └───────────────┘
        ↓                  ↓                  ↓
   scan_project()  parse_python_file() extract_relations()
   (scanner.py)     (parser_python.py)  (relations.py)
```

---

## 2. Composants

### 2.1 Scanner (`scanner.py`)
**Responsabilité** : Parcourir récursivement un dossier et identifier les fichiers source.

**Clés**:
- Filtrage des dossiers ignorés (`__pycache__`, `.git`, `venv`, etc.)
- Filtrage des extensions (`.py` pour Python)
- Exclusion des fichiers de test par défaut
- Limitation de taille (500 KB max)

**Sortie** :
```python
[
    {
        "path": "models/user.py",           # chemin relatif
        "abs_path": "/full/path/...",       # chemin absolu
        "size_bytes": 2500,
    },
    ...
]
```

### 2.2 Parser (`parser_python.py`)
**Responsabilité** : Parser chaque fichier Python et extraire les entités.

**Technologie** : Tree-sitter (`tree-sitter-python`)
- Parsing syntaxique robuste (gère les erreurs)
- Production d'un arbre syntaxique concret (CST)
- Idéal pour les fichiers malformés

**Entités extraites** :
- **Classes** : nom, méthodes, classe parente, décorateurs, docstring
- **Fonctions** : nom, arguments (typés ou non), type de retour, async?, décorateurs
- **Arguments** : nom, type optionnel, valeur par défaut
- **Imports** : `import X` ou `from X import Y`
- **Variables globales** : constantes de module

**Sortie** :
```python
FileAnalysis(
    path="models.py",
    size_bytes=2500,
    total_lines=78,
    classes=[ClassEntity(...), ...],
    functions=[FunctionEntity(...), ...],
    imports=[ImportEntity(...), ...],
    global_variables=[GlobalVariable(...), ...],
    error=None,  # ou message d'erreur
)
```

### 2.3 Relations (`relations.py`)
**Responsabilité** : Détecter les dépendances entre entités.

**Types de relations** :
1. **Import** : Fichier A importe une classe/fonction de Fichier B
2. **Inheritance** : Classe A hérite de Classe B

**Stratégie** :
- Construire des index (classes par nom, fonctions par nom)
- Parcourir les imports → résoudre vers les entités
- Parcourir les héritage → résoudre vers les classes

**Sortie** :
```python
[
    Relation(
        from_entity="main.py",
        from_file="main.py",
        to_entity="User",
        to_file="models.py",
        type="import",
    ),
    Relation(
        from_entity="AdminUser",
        from_file="models.py",
        to_entity="User",
        to_file="models.py",
        type="inheritance",
    ),
]
```

### 2.4 Analyzer (`analyzer.py`)
**Responsabilité** : Orchestrer les 3 phases précédentes.

**Fonction clé** : `analyze_project(project_path, language="python")`
1. Scan récursif des fichiers
2. Parsing de chaque fichier Python
3. Extraction des relations
4. Construction de `ProjectAnalysis`
5. Sérialisation JSON

---

## 3. Décisions de design

### 3.1 Pourquoi Tree-sitter ?

| Critère | AST stdlib | Tree-sitter |
|---------|-----------|-------------|
| **Robustesse** | ❌ Crash sur erreur | ✅ Parse partiellement |
| **Erreurs** | Tout ou rien | Marque les erreurs |
| **Performance** | Lent | Très rapide (C) |
| **Multi-langage** | Non | Oui (extensible) |

**Choix** : Tree-sitter pour sa robustesse sur des codebases réelles.

### 3.2 Extraction des arguments typés

Tree-sitter distingue plusieurs nœuds pour les arguments :
- `identifier` : argument simple
- `typed_parameter` : nom + type
- `default_parameter` : nom + valeur par défaut
- `typed_default_parameter` : nom + type + défaut
- `list_splat_pattern` : `*args`
- `dictionary_splat_pattern` : `**kwargs`

Le parser extraits tous les cas et crée un `FunctionArg` pour chacun.

### 3.3 Détection async

**Défi** : L'async peut être à deux niveaux :
```python
@decorator
async def func():  # ← async ici (decorat niveau)
    pass

async def func():  # ← async ici (function niveau)
    pass
```

**Solution** : Vérifier async au niveau de la `decorated_definition` ET au niveau de `function_definition`.

### 3.4 Index pour résolutions de noms

Pour les imports et l'héritage, il faut résoudre les noms vers des entités réelles.

Stratégie :
```python
class_by_name = {}  # "User" → "models.py"
function_by_name = {}  # "main" → "main.py"

# Puis pour "from models import User"
if "User" in class_by_name:
    to_file = class_by_name["User"]  # "models.py"
```

---

## 4. Gestion des erreurs

| Situation | Comportement |
|-----------|-------------|
| Fichier avec erreur syntaxe | Continue, marque error dans FileAnalysis |
| Dossier inexistant | Lève FileNotFoundError |
| Langage non supporté | Lève ValueError |
| Import à module externe | Relation créée avec to_file=None |
| Classe parente non trouvée | Loggé en warning, pas de crash |

---

## 5. Limitations actuelles (Sprint 1)

### ✅ Implémenté
- Extraction de classes, méthodes, fonctions
- Arguments typés, valeurs par défaut
- Décorateurs et docstrings
- Imports simples et from imports
- Variables globales
- Relations import et inheritance

### ⏳ Planifié (Sprint 2+)
- **Appels de fonction** : Détecter `func()` → dépendance dynamique
- **Langages additionnels** : JavaScript, Java, Go, Rust
- **Imports conditionnels** : `if TYPE_CHECKING: from X import Y`
- **Type hints complexes** : `Union`, `Generic`, annotations en string
- **Annotations de propriété** : `@property`, `@classmethod`

---

## 6. Tests

### Structure
```
tests/
├── test_scanner.py       (scan_project, get_project_name)
├── test_parser.py        (parse_python_file)
├── test_entities.py      (dataclasses)
├── test_relations.py     (extract_relations)
├── test_integration.py   (analyze_project E2E)
└── fixtures/
    └── sample_project/   (mini-projet pour tests)
        ├── models.py
        ├── main.py
        └── broken_file.py
```

### Exécution
```bash
cd forgegraph
pytest tests/ -v
pytest tests/ -v --cov=analyzer --cov-report=html
```

### Couverture cible
- Scanner : 95%+ (tous les cas de filtrage)
- Parser : 90%+ (toutes les formes d'entités)
- Relations : 85%+ (imports et inheritance)
- Integration : 80%+ (E2E)

---

## 7. Exemple d'utilisation

### Utilisation simple
```python
from analyzer import analyze_project
import json

result = analyze_project("/path/to/my/project")

# Accès aux résultats
print(f"Classes: {result['stats']['total_classes']}")
print(f"Fonctions: {result['stats']['total_functions']}")

# Sauvegarder en JSON
with open("analysis.json", "w") as f:
    json.dump(result, f, indent=2)
```

### Utilisation avancée
```python
from analyzer import scan_project, parse_python_file, extract_relations

# Phase 1: Scanner
files = scan_project(project_path, language="python")

# Phase 2: Parser
analyses = [parse_python_file(f["abs_path"]) for f in files]

# Phase 3: Relations
relations = extract_relations(analyses)
```

---

## 8. Architecture pour l'intégration avec Mimoun

`analyze_project()` retourne un dictionnaire JSON structuré selon la spécification de `interface_analyse.md`.

**Format de sortie** :
```json
{
  "project_name": "chatnow",
  "language": "python",
  "analyzed_at": "2026-04-24T10:30:00Z",
  "stats": {
    "total_files": 15,
    "total_classes": 12,
    "total_functions": 48,
    "total_imports": 95,
    "total_methods": 67,
    "files_with_errors": 0
  },
  "files": [
    {
      "path": "app/models/user.py",
      "size_bytes": 3107,
      "total_lines": 78,
      "classes": [ ... ],
      "functions": [ ... ],
      "imports": [ ... ],
      "global_variables": [ ... ],
      "error": null
    }
  ],
  "relations": [
    {
      "from_entity": "User",
      "from_file": "app/models/user.py",
      "to_entity": "BaseModel",
      "to_file": "app/models/base.py",
      "type": "inheritance"
    }
  ]
}
```

**Interface à fournir à Mimoun** :
```python
def analyze_project(project_path: str, language: str = "python") -> dict
```

Le dictionnaire JSON est prêt pour être consommé par le LangGraph de Mimoun.

---

## 9. Notes de maintenance

### Pour déboguer un parser mal formé
```python
from analyzer.parser_python import parse_python_file
result = parse_python_file("problematic_file.py")
print(f"Error: {result.error}")
print(f"Classes found: {len(result.classes)}")
print(f"Functions found: {len(result.functions)}")
```

### Pour voir la structure tree-sitter
```python
import tree_sitter_python as tspython
from tree_sitter import Language, Parser

lang = Language(tspython.language())
parser = Parser(lang)
tree = parser.parse(b"code here")
print(tree.root_node)  # Voir la structure
```

### Logging
```python
import logging
logging.basicConfig(level=logging.DEBUG)
result = analyze_project(project_path)  # Verra tous les logs
```

---

## 10. Checklist de qualité

- [x] Types hints complets (`from __future__ import annotations`)
- [x] Docstrings PEP 257
- [x] Gestion cohérente des erreurs
- [x] Logging structuré
- [x] Tests unitaires complets
- [x] Test d'intégration E2E
- [x] Pas de code mort/commenté
- [x] Pas de hardcoding de chemins
- [x] Sortie JSON valide

---

## Contacts & Références

**Documentation** :
- `docs/interface_analyse.md` : Spécification complète du JSON
- `docs/recherche_outils_parsing.md` : Notes de recherche sur Tree-sitter
- `README.md` : Utilisation basique

**Dépendances** :
- `tree-sitter` : Parseur multi-langage
- `tree-sitter-python` : Binding pour Python
- `pytest` : Framework de test

