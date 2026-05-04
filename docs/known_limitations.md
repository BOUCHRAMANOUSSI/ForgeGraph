# ⚠️ Limitations Connues

> **Date** : 2026-04-24  
> **Sprint** : Sprint 1

---

## 1. Limitations du Parser Python (Tree-sitter)

### 1.1 Type hints complexes
**Problème** : Les type hints avancés ne sont pas totalement parsés.

**Exemples** :
```python
def func(x: Union[str, int]) -> Optional[Dict[str, List[int]]]:
    pass
```

**Comportement actuel** :
- Type capturé comme texte brut : `"Union[str, int]"`
- Pas de décomposition en Union, Optional, etc.

**Impact** : Les analyses de compatibilité de type seront limitées (Sprint 2).

**Workaround** : Accepter les types comme strings; l'IA peut les interpréter.

---

### 1.2 Annotations en string
**Problème** : Les annotations différées (PEP 563) ne sont pas traitées spécifiquement.

```python
from __future__ import annotations

def func(x: MyClass) -> AnotherClass:
    pass
```

**Comportement actuel** :
- Pas de résolution des noms → pas de relation créée
- Les types sont capturés textuels

**Impact** : Certaines relations d'héritage/type ne seront pas détectées.

**Workaround** : Implémenter une phase 2 de résolution des annotations.

---

### 1.3 Decorators avec arguments complexes
**Problème** : Les décorateurs avec paramètres ne sont pas complètement parsés.

```python
@decorator(arg1=value1, arg2=value2)
def func():
    pass
```

**Comportement actuel** :
- Nom du décorateur capturé : `"decorator"`
- Arguments du décorateur : ignorés

**Impact** : Pas d'information sur les paramètres du décorateur.

**Workaround** : Sprint 2, si nécessaire.

---

### 1.4 Imports relatifs (..)
**Problème** : Les imports relatifs ne sont pas totalement résolus.

```python
from ..parent.module import MyClass
from . import sibling
```

**Comportement actuel** :
- Import capturé comme `"..parent.module"`
- Pas de résolution du chemin réel (relativité du contexte)

**Impact** : Relations d'import incomplet pour imports relatifs.

**Priorité** : Faible (peu courant dans petits projets).

---

### 1.5 Propriétés (@property)
**Problème** : Les propriétés sont traitées comme des méthodes.

```python
@property
def value(self) -> int:
    return self._value
```

**Comportement actuel** :
- Traité comme une méthode normale
- Décorateur `@property` détecté mais pas d'indication spéciale
- Pas d'information sur la sémantique (getter, setter)

**Impact** : Pas de distinction entre méthodes et propriétés.

**Workaround** : Vérifier le décorateur pour identifier les propriétés.

---

## 2. Limitations des Relations

### 2.1 Appels de fonction (call graph)
**Problème** : Les appels de fonction ne sont pas détectés.

```python
def main():
    result = process_data(x)  # ← On ne sait pas que process_data est appelée
```

**Comportement actuel** :
- Relation `call` non implémentée
- Pas d'information sur les dépendances dynamiques

**Impact** : Analyse de flot de données incomplète.

**Priorité** : Sprint 2.

**Raison** : Nécessite du data flow analysis complexe.

---

### 2.2 Imports dynamiques (eval, __import__)
**Problème** : Les imports générés dynamiquement ne peuvent pas être détectés.

```python
module_name = "user"
User = __import__(f"models.{module_name}").User
```

**Comportement actuel** :
- Code pas exécuté, pas d'analyse statique possible
- Import ignoré

**Impact** : Dépendances masquées dans le graph.

**Workaround** : Documenter les imports dynamiques en commentaires.

---

### 2.3 Dépendances circulaires
**Problème** : Les références circulaires ne sont pas détectées.

```python
# models.py
from views import MyView  # ← Crée une relation

# views.py  
from models import MyModel  # ← Crée une relation circulaire
```

**Comportement actuel** :
- Toutes les relations sont créées (y compris les circulaires)
- Pas d'alerte spéciale

**Impact** : À Mimoun de détecter les cycles.

**Workaround** : Utiliser un algo de détection de cycle (DFS) chez Mimoun.

---

## 3. Limitations du Scanner

### 3.1 Chemins Windows vs Unix
**Problème** : Les chemins utilisent `\` sur Windows et `/` sur Unix.

**Comportement actuel** :
- `path` (relatif) : Format POSIX (`/`) sur tous les OS
- `abs_path` : Format natif de l'OS

**Impact** : Nécessité de normalisation chez le consommateur.

**Workaround** : Utiliser `pathlib.Path` pour cross-platform.

---

### 3.2 Fichiers symlink
**Problème** : Les symbolic links ne sont pas suivis.

**Comportement actuel** :
- Symlinks ignorés lors du scan

**Impact** : Certains fichiers ne seront pas analysés.

**Workaround** : Résoudre les symlinks avant appel de scan.

---

### 3.3 Taille maximale de fichier
**Problème** : Les fichiers > 500 KB sont ignorés.

**Comportement actuel** :
- Fichiers volumineux skippés avec warning

**Impact** : Grands fichiers générés non analysés (normal).

**Workaround** : Augmenter `MAX_FILE_SIZE_BYTES` si nécessaire.

---

## 4. Limitations des Entités

### 4.1 Docstrings tronquées
**Problème** : Les docstrings > 200 chars sont tronquées.

**Comportement actuel** :
```python
docstring = first_line[:200] + "..."
```

**Impact** : Perte d'information pour docstrings longues.

**Workaround** : Augmenter la limite si full text needed.

---

### 4.2 Valeurs de variable partielles
**Problème** : Les assignations complexes ne sont pas totalement capturées.

```python
CONFIG = {
    "host": "localhost",
    "port": 5000,
}  # ← Valeur partiellement capturée
```

**Comportement actuel** :
- Valeur tronquée à 100 chars

**Impact** : Info partielle sur les constantes.

**Workaround** : Vérifier le fichier source pour détails complets.

---

## 5. Limitations d'Encodage

### 5.1 Encodage non-UTF8
**Problème** : Certains fichiers utilisent d'autres encodages.

**Comportement actuel** :
1. Tente UTF-8
2. Fallback sur latin-1 si erreur
3. Skip le fichier en cas de problème

**Impact** : Quelques fichiers mal encodés non analysés.

**Workaround** : Convertir les encodages avant analyse.

---

## 6. Limitations Multi-langage

### 6.1 Langage non supporté
**Problème** : Seulement Python en Sprint 1.

**Langage supportés** :
| Langage | Sprint | Status |
|---------|--------|--------|
| Python | 1 | ✅ Implémenté |
| JavaScript | 2+ | ⏳ Planifié |
| Java | 3+ | ⏳ Planifié |
| Go | 4+ | ⏳ Planifié |

**Impact** : Impossible d'analyser des projets multi-langages.

**Workaround** : Analyser chaque langage séparément.

---

## 7. Limitations de Performance

### 7.1 Grands projets (1000+ fichiers)
**Problème** : Performances dégradées sur très gros codebases.

**Comportement estimé** :
- 100 fichiers : ~1-2 secondes
- 1000 fichiers : ~10-20 secondes
- 10000 fichiers : Minutes

**Impact** : Timeouts possibles sur très gros projets.

**Workaround** : Implémenter parallelisation (Sprint 2).

---

### 7.2 Mémoire
**Problème** : La structure JSON peut être volumineux pour gros projets.

**Comportement** :
- Chaque entité = dict + listes
- Grands projets = plusieurs MB en RAM

**Impact** : Possibilité de saturation sur petites machines.

**Workaround** : Streaming ou pagination (Sprint 2).

---

## 8. Limitations de Sécurité

### 8.1 Pas de détection de vulnérabilités
**Problème** : Pas d'analyse de sécurité.

**Comportement** :
- Aucune détection de problème sécu
- Aucune vérification de dépendances dangereuses

**Impact** : Sécurité responsabilité de l'utilisateur.

**Workaround** : Intégrer tools externes (bandit, semgrep).

---

### 8.2 Injection de code
**Problème** : Pas de sandboxing, code peut être malveillant.

**Comportement** :
- Les fichiers Python analysés ne sont pas exécutés
- Seulement parsing AST/CST

**Impact** : Sûr, pas de risque d'exécution.

---

## 9. Roadmap de Résolution

### Sprint 2
- [ ] Détection des appels de fonction
- [ ] Support JavaScript/TypeScript
- [ ] Imports relatifs résolus
- [ ] Parallelization du parsing

### Sprint 3
- [ ] Support Java
- [ ] Détection des imports dynamiques
- [ ] Analyse de flot de données basique
- [ ] Cache des analyses

### Sprint 4+
- [ ] Support Go, Rust, C#
- [ ] Détection de vulnérabilités
- [ ] Graphe dépendances visuel
- [ ] API GraphQL

---

## 10. Feedback & Issues

Pour signaler une limitation non documentée :
1. Ouvrir une issue GitHub
2. Inclure le cas d'usage concret
3. Patch optional mais apprécié

---
