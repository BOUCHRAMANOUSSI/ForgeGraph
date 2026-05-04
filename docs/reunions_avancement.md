# 🗣️ Script pour les Réunions d'Avancement (Daily Scrum)

> **Pour Bouchra** : Voici ce que tu peux dire chaque jour lors de la réunion de synchronisation avec ton encadrant, Mimoun et Abdelhakim. Chaque point suit le format classique : *Ce que j'ai fait hier*, *Ce que je fais aujourd'hui*, *Mes points de blocage (s'il y en a)*.

---

## 📅 Jour 1 (Mardi) — Lancement & Recherche

**Ce que tu peux dire :**
> "Bonjour à tous. Hier (Jour 1), je me suis concentrée sur la compréhension du besoin pour mon module d'Analyse et Ingestion. J'ai étudié les différentes entités qu'on doit extraire du code (classes, fonctions, méthodes, imports, etc.) et j'ai fait des recherches sur les outils de parsing. J'ai rédigé un document comparatif entre `ast` natif en Python et `tree-sitter`.
> Aujourd'hui, je vais travailler sur la définition exacte du schéma JSON que je vais envoyer à Mimoun. On va devoir se caler là-dessus.
> Pas de point de blocage pour le moment."

---

## 📅 Jour 2 (Mercredi) — Définition des Interfaces

**Ce que tu peux dire :**
> "Hier, j'ai défini toute l'interface de communication de mon module. J'ai créé un schéma JSON complet et très détaillé qui décrit comment je vais structurer les fichiers, les classes, les fonctions et leurs relations. J'ai documenté tout ça dans `interface_analyse.md`. J'en ai profité pour valider ce format avec Mimoun pour être sûre que son LangGraph puisse le lire facilement.
> Aujourd'hui, je vais attaquer le code : créer la structure du module, définir mes `dataclasses` (les modèles de données en Python) et coder le scanner de fichiers qui va parcourir le dossier fourni par Abdelhakim.
> Pas de blocage."

---

## 📅 Jour 3 (Jeudi) — Structure & Scanner

**Ce que tu peux dire :**
> "Hier, j'ai mis en place l'architecture de mon module. J'ai codé le fichier `entities.py` avec toutes les structures de données (10 dataclasses au total). Ensuite, j'ai développé et testé le `scanner.py` : il est capable de parcourir un projet de façon récursive, d'ignorer les dossiers inutiles comme `__pycache__` ou `node_modules`, et de lister les fichiers sources valides. J'ai aussi mis en place les premiers tests unitaires avec `pytest`.
> Aujourd'hui, c'est la grosse étape : je commence le parsing du code source avec Tree-sitter pour extraire les classes et les fonctions.
> Petit point de vigilance : l'installation de Tree-sitter demande des bibliothèques C, mais ça s'est bien passé sur mon poste."

---

## 📅 Jour 4 (Vendredi) — Parsing Tree-sitter (Le Cœur du Module)

**Ce que tu peux dire :**
> "Hier, j'ai fait une grosse avancée. J'ai implémenté le parser complet (`parser_python.py`) en utilisant **Tree-sitter** comme demandé dans les exigences. Le parser est capable de lire l'arbre syntaxique et d'extraire parfaitement les classes, les méthodes, les fonctions (même asynchrones), les imports et les variables globales. J'ai aussi géré les cas complexes comme l'extraction des arguments, des valeurs par défaut et des décorateurs. Tous mes tests unitaires passent (28 tests au vert). J'ai même fait un test grandeur nature sur le backend de notre ancien projet ChatNow et ça a marché du premier coup !
> Aujourd'hui (ou Lundi prochain), je vais finaliser l'extraction des relations (pour savoir si tel fichier importe telle classe) et préparer le script de démo final.
> Pas de blocage, le module est très stable."

---

## 📅 Jour 5 (Lundi prochain) — Intégration & Finalisation Sprint 1

*(À utiliser la semaine prochaine, quand on aura fini les relations et le CLI)*

**Ce que tu peux dire :**
> "Hier, j'ai finalisé la détection des relations entre les entités (comme l'héritage et les imports croisés). J'ai aussi créé le script principal en ligne de commande pour que le module soit facilement utilisable. J'ai rédigé la documentation technique finale expliquant comment j'ai implémenté Tree-sitter.
> Aujourd'hui, mon module est prêt. Je vais travailler avec Abdelhakim pour tester l'analyse d'un code téléchargé depuis son conteneur Docker, et avec Mimoun pour faire un test de bout en bout de notre pipeline ForgeGraph. On est bons pour la démo de fin de sprint !"
