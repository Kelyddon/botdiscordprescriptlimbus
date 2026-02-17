# Bot Discord Prescript — botindexprescripte

## Sommaire / Table of Contents

- [🇫🇷 Version française](#fr)
	- [1) Présentation](#fr-1)
	- [2) Fonctionnalités](#fr-2)
	- [3) Installation](#fr-3)
	- [4) Configuration](#fr-4)
	- [5) Lancement](#fr-5)
	- [6) Commandes à entrer](#fr-6)
	- [7) Structure du code](#fr-7)
	- [8) Comment modifier le bot](#fr-8)
	- [9) Inspiration et crédits](#fr-9)
	- [10) Dépannage rapide](#fr-10)
- [🇬🇧 English version](#en)
	- [1) Overview](#en-1)
	- [2) Features](#en-2)
	- [3) Installation](#en-3)
	- [4) Configuration](#en-4)
	- [5) Run](#en-5)
	- [6) Commands to run](#en-6)
	- [7) Code structure](#en-7)
	- [8) How to customize](#en-8)
	- [9) Inspiration and credits](#en-9)
	- [10) Quick troubleshooting](#en-10)

<a id="fr"></a>
## 🇫🇷 Version française

<a id="fr-1"></a>
### 1) Présentation
Bot Discord Python inspiré du concept de « Prescript » : génération de phrases, affichage progressif (machine à écrire), styles visuels et commandes de contrôle.

<a id="fr-2"></a>
### 2) Fonctionnalités
- Commandes : `/prescript`, `/pause_prescript`, `/resume_prescript`, `/stop_prescript`
- Commandes hybrides : disponibles aussi en préfixe `!`
- Modes de rendu : bloc code, embed, image (optionnel via Playwright)
- Styles : `plain`, `spaced`, `ascii`, `glitch` (non utilisé par défaut en aléatoire)

<a id="fr-3"></a>
### 3) Installation (Windows PowerShell)
```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

<a id="fr-4"></a>
### 4) Configuration
Créer un fichier `.env` à la racine :
```env
DISCORD_TOKEN=VOTRE_TOKEN_ICI
```

<a id="fr-5"></a>
### 5) Lancement
```powershell
python bot.py
```
Ou explicitement avec la venv :
```powershell
.\.venv\Scripts\python.exe bot.py
```

Options utiles :
- `--debug`
- `--dev-guild <ID_GUILDE>`
- `--no-sync`
- `--token <TOKEN>`

<a id="fr-6"></a>
### 6) Commandes à entrer (copier-coller)
Préparer l'environnement + dépendances :
```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

Définir le token pour la session :
```powershell
$env:DISCORD_TOKEN="VOTRE_TOKEN_ICI"
```

Démarrer le bot :
```powershell
python bot.py
```

Lancer les tests :
```powershell
.\.venv\Scripts\python.exe -m pytest -q
```

Exemples de commandes Discord :
```text
/prescript
/prescript embed:true title:"Prescript" embed_color:#7D3CFF
/prescript style:ascii
/pause_prescript
/resume_prescript
/stop_prescript
```

<a id="fr-7"></a>
### 7) Structure du code
- `bot.py` : point d'entrée, options CLI, chargement du cog, sync des commandes
- `cogs/prescript.py` : commandes Discord + affichage progressif
- `utils/prescript_generator.py` : génération procédurale des phrases
- `utils/text_manager.py` : chargement/sélection des prescripts JSON
- `utils/style.py` : styles et transformations visuelles
- `utils/state.py` : état pause/reprise/arrêt
- `utils/renderer.py` : rendu image optionnel
- `data/prescript.json` : contenu modifiable (`fr.prescripts`, `en.prescripts`, `en.pools`)

<a id="fr-8"></a>
### 8) Comment modifier le bot
- Modifier les phrases : `data/prescript.json`
- Modifier le rendu/stylisation : `utils/style.py`
- Modifier la logique de génération : `utils/prescript_generator.py`
- Modifier le comportement Discord : `cogs/prescript.py`

<a id="fr-9"></a>
### 9) Inspiration et crédits
Ce projet est inspiré de :
- NYOS-cat / NYOS : https://github.com/NYOS-cat/NYOS
- Fichier de référence : https://github.com/NYOS-cat/NYOS/blob/main/prescript.js

Le projet est aussi inspiré de l'univers de **Limbus Company**, en particulier **The Index**.

> Projet fan-made inspiré, non officiel.

<a id="fr-10"></a>
### 10) Dépannage rapide
- `ModuleNotFoundError: discord` : installer les dépendances dans la bonne venv
- `MissingApplicationID` : utiliser `--dev-guild` ou relancer après connexion complète
- `PyNaCl is not installed` : requis seulement pour certaines fonctionnalités vocales
- Avertissement `audioop` : warning connu côté dépendance `discord.py`

---

<a id="en"></a>
## 🇬🇧 English version

<a id="en-1"></a>
### 1) Overview
Python Discord bot inspired by the “Prescript” concept: sentence generation, progressive typewriter rendering, visual styles, and control commands.

<a id="en-2"></a>
### 2) Features
- Commands: `/prescript`, `/pause_prescript`, `/resume_prescript`, `/stop_prescript`
- Hybrid commands: also available with `!` prefix
- Render modes: code block, embed, image (optional via Playwright)
- Styles: `plain`, `spaced`, `ascii`, `glitch` (`glitch` is not randomly selected by default)

<a id="en-3"></a>
### 3) Installation (Windows PowerShell)
```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

<a id="en-4"></a>
### 4) Configuration
Create a `.env` file at project root:
```env
DISCORD_TOKEN=YOUR_TOKEN_HERE
```

<a id="en-5"></a>
### 5) Run
```powershell
python bot.py
```
Or explicitly with venv Python:
```powershell
.\.venv\Scripts\python.exe bot.py
```

Useful options:
- `--debug`
- `--dev-guild <GUILD_ID>`
- `--no-sync`
- `--token <TOKEN>`

<a id="en-6"></a>
### 6) Commands to run (copy/paste)
Environment + dependencies:
```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

Set token for current shell session:
```powershell
$env:DISCORD_TOKEN="YOUR_TOKEN_HERE"
```

Start bot:
```powershell
python bot.py
```

Run tests:
```powershell
.\.venv\Scripts\python.exe -m pytest -q
```

Discord command examples:
```text
/prescript
/prescript embed:true title:"Prescript" embed_color:#7D3CFF
/prescript style:ascii
/pause_prescript
/resume_prescript
/stop_prescript
```

<a id="en-7"></a>
### 7) Code structure
- `bot.py`: entrypoint, CLI options, cog loading, command sync
- `cogs/prescript.py`: Discord commands + progressive rendering
- `utils/prescript_generator.py`: procedural text generation
- `utils/text_manager.py`: JSON loading/selection logic
- `utils/style.py`: style transforms
- `utils/state.py`: pause/resume/stop state handling
- `utils/renderer.py`: optional image rendering
- `data/prescript.json`: editable content (`fr.prescripts`, `en.prescripts`, `en.pools`)

<a id="en-8"></a>
### 8) How to customize
- Edit phrases/content: `data/prescript.json`
- Edit rendering styles: `utils/style.py`
- Edit generation logic: `utils/prescript_generator.py`
- Edit Discord behavior: `cogs/prescript.py`

<a id="en-9"></a>
### 9) Inspiration and credits
Inspired by:
- NYOS-cat / NYOS: https://github.com/NYOS-cat/NYOS
- Reference file: https://github.com/NYOS-cat/NYOS/blob/main/prescript.js

Also inspired by **Limbus Company**, especially **The Index** aesthetic/concept.

> This is an inspired fan-made project, not an official product.

<a id="en-10"></a>
### 10) Quick troubleshooting
- `ModuleNotFoundError: discord`: install dependencies in the correct venv
- `MissingApplicationID`: use `--dev-guild` or retry after full ready/login
- `PyNaCl is not installed`: needed only for some voice features
- `audioop` warning: known warning from `discord.py` dependency
