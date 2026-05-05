# 📐 Interface du Module Analyse & Ingestion

> **Auteur** : Bouchra  
> **Version** : 1.0  


---

## 1. Vue d'ensemble

Le module **Analyse & Ingestion** reçoit un chemin vers un dossier de code source
et produit un **document JSON structuré** contenant toutes les entités et relations
extraites du code.

```
┌─────────────────┐         ┌──────────────────────┐         ┌─────────────────┐
│   Abdelhakim     │         │      Bouchra          │         │     Mimoun       │
│   (Docker)       │────────►│  (Analyse & Ingestion)│────────►│  (LangGraph)     │
│                  │  chemin │                       │  JSON   │                  │
│  Clone le repo   │  du     │  Parse le code        │  des    │  Orchestre l'IA  │
│  dans un volume  │  dossier│  Extrait les entités  │  entités│  Décide quoi     │
│  Docker          │         │  Détecte les relations│         │  analyser        │
└─────────────────┘         └──────────────────────┘         └─────────────────┘
```

## 2. Interface d'entrée

### 2.1 Fonction principale

```python
def analyze_project(project_path: str, language: str = "python") -> dict:
    """
    Point d'entrée principal du module d'analyse.
    
    Args:
        project_path: Chemin absolu vers le dossier du projet à analyser.
                      Fourni par le module Infrastructure (Abdelhakim).
        language:     Langage cible ("python" pour le Sprint 1).
    
    Returns:
        Dictionnaire conforme au schéma JSON défini en §3.
    """
```


### 2.3 Pré-conditions

- Le dossier `project_path` **doit exister** et être **lisible**
- Le module Infrastructure (Abdelhakim) est responsable de garantir l'accès au dossier
- Les fichiers avec des erreurs de syntaxe seront **ignorés** (skip, pas crash)

---

## 3. Schéma JSON de sortie

### 3.1 Structure racine

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
    "files_with_errors": 0
  },
  "files": [ ... ],
  "relations": [ ... ]
}
```

### 3.2 Objet `File`

```json
{
  "path": "app/routers/users.py",
  "size_bytes": 3107,
  "total_lines": 78,
  "classes": [ ... ],
  "functions": [ ... ],
  "imports": [ ... ],
  "global_variables": [ ... ]
}
```

### 3.3 Objet `Class`

```json
{
  "name": "VectorStoreService",
  "line_start": 21,
  "line_end": 118,
  "decorators": [],
  "base_classes": [],
  "docstring": "Service responsable du découpage des textes en petits Chunks...",
  "methods": [
    {
      "name": "chunk_and_store",
      "args": [
        {"name": "db", "type": "AsyncSession"},
        {"name": "document_id", "type": "int"},
        {"name": "full_text", "type": "str"}
      ],
      "return_type": "int",
      "is_async": true,
      "decorators": [],
      "docstring": "Découpe un texte complet et le vectorise en BDD.",
      "line_start": 35,
      "line_end": 61
    }
  ]
}
```

### 3.4 Objet `Function` (top-level, hors classe)

```json
{
  "name": "trim_history",
  "args": [
    {"name": "messages", "type": "list[LLMMessage]"},
    {"name": "max_tokens", "type": "int", "default": "8000"}
  ],
  "return_type": "list[LLMMessage]",
  "is_async": false,
  "decorators": [],
  "docstring": "S'assure que l'historique ne dépasse jamais la limite de tokens.",
  "line_start": 99,
  "line_end": 117
}
```

### 3.5 Objet `Import`

```json
{
  "type": "from",
  "module": "app.services.vector_store_service",
  "names": ["vector_store_service"],
  "line": 403
}
```

Ou pour un import simple :

```json
{
  "type": "import",
  "module": "logging",
  "names": [],
  "line": 3
}
```

### 3.6 Objet `GlobalVariable`

```json
{
  "name": "_DEFAULT_OFFLINE_MODEL",
  "value": "ollama/phi3",
  "line": 121
}
```

### 3.7 Objet `Relation`

```json
{
  "from_entity": "AuthService",
  "from_file": "app/services/auth.py",
  "to_entity": "User",
  "to_file": "app/models/user.py",
  "type": "import"
}
```

**Types de relations supportés :**

| Type | Description | Exemple |
|------|-------------|---------|
| `import` | Un fichier importe une entité d'un autre | `from app.models import User` |
| `inheritance` | Une classe hérite d'une autre | `class Dog(Animal)` |
| `call` | Une fonction appelle une autre fonction | `result = hash_password(pwd)` |

---

## 4. Gestion des erreurs

| Situation | Comportement |
|-----------|-------------|
| Fichier avec erreur de syntaxe | Skip le fichier, ajouté à `files_with_errors` |
| Dossier inexistant | Lève `FileNotFoundError` |
| Fichier binaire | Ignoré automatiquement |
| Encodage non-UTF8 | Tentative avec `latin-1`, sinon skip |

## 5. Langages supportés



---

## 6. Exemple complet de sortie

Résultat attendu en analysant un mini-projet Python :

```json
{
  "project_name": "mini-projet",
  "language": "python",
  "analyzed_at": "2026-04-24T10:30:00Z",
  "stats": {
    "total_files": 2,
    "total_classes": 1,
    "total_functions": 2,
    "total_imports": 3,
    "files_with_errors": 0
  },
  "files": [
    {
      "path": "main.py",
      "size_bytes": 450,
      "total_lines": 20,
      "classes": [],
      "functions": [
        {
          "name": "main",
          "args": [],
          "return_type": null,
          "is_async": false,
          "decorators": [],
          "docstring": "Point d'entrée principal.",
          "line_start": 5,
          "line_end": 10
        }
      ],
      "imports": [
        {"type": "from", "module": "models", "names": ["User"], "line": 1}
      ],
      "global_variables": []
    },
    {
      "path": "models.py",
      "size_bytes": 300,
      "total_lines": 15,
      "classes": [
        {
          "name": "User",
          "line_start": 3,
          "line_end": 15,
          "decorators": ["dataclass"],
          "base_classes": [],
          "docstring": "Représente un utilisateur.",
          "methods": [
            {
              "name": "full_name",
              "args": [{"name": "self", "type": null}],
              "return_type": "str",
              "is_async": false,
              "decorators": ["property"],
              "docstring": null,
              "line_start": 10,
              "line_end": 12
            }
          ]
        }
      ],
      "functions": [],
      "imports": [
        {"type": "from", "module": "dataclasses", "names": ["dataclass"], "line": 1}
      ],
      "global_variables": []
    }
  ],
  "relations": [
    {
      "from_entity": "main.py",
      "from_file": "main.py",
      "to_entity": "User",
      "to_file": "models.py",
      "type": "import"
    }
  ]
}
```
