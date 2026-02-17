"""Gestion du chargement et de la sélection de prescripts depuis JSON.

Ce module fournit:
- une normalisation d'entrées hétérogènes (str / dict),
- un gestionnaire `PrescriptManager` avec plusieurs modes de sélection,
- un wrapper rétrocompatible `charger_prescripts`.
"""

import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Union
import random


def _normalize_entry(entry: Any) -> Dict[str, Any]:
	"""Normalise une entrée en structure homogène `{id, text, weight}`.

	Formats acceptés:
	- `"texte"`
	- `{ "text": "..." }` (ou `value` / `label`)
	- `{ "id": ..., "text": ..., "weight": ... }`
	"""
	if isinstance(entry, str):
		return {"id": None, "text": entry, "weight": 1}
	if isinstance(entry, dict):
		text = entry.get("text") or entry.get("value") or entry.get("label")
		if text is None:
			# if dict contains only one key with string value, use it
			for v in entry.values():
				if isinstance(v, str):
					text = v
					break
		if text is None:
			raise TypeError("Prescript entry dict must contain a text/value/label string")
		return {"id": entry.get("id"), "text": text, "weight": float(entry.get("weight", 1))}
	raise TypeError("Prescript entries must be either strings or dicts")


class PrescriptManager:
	"""Charge et gère des prescripts avec plusieurs modes de sélection.

	Fonctionnalités:
	- Accepte une liste simple de chaînes ou une liste d'objets (`text`, `weight`, `id`).
	- Supporte un encapsulage par langue: {"fr": {"prescripts": [...]}}
	- Modes de sélection: aléatoire, pondéré, séquentiel, par index, par identifiant.
	- Expansion simple de placeholders via `.format(**context)`.
	"""

	def __init__(self, prescripts: List[Union[str, Dict[str, Any]]], language: str = "fr"):
		# Données source brutes, conservées pour debug/introspection
		self._raw = prescripts
		# Version normalisée (shape stable pour les méthodes de sélection)
		self._items = [_normalize_entry(e) for e in prescripts]
		# Pointeur interne pour la sélection séquentielle circulaire
		self._seq_index = 0
		# Langue associée au chargement
		self.language = language

	@classmethod
	def load_from_file(cls, fichier_json: str = "data/prescript.json", langue: str = "fr") -> "PrescriptManager":
		"""Charge un manager depuis un fichier JSON.

		Structures supportées:
		- `{ "fr": { "prescripts": [...] }, "en": ... }`
		- `{ "prescripts": [...] }`
		- `[...]` (liste brute)
		"""
		p = Path(fichier_json)
		if not p.exists():
			raise FileNotFoundError(f"Fichier {fichier_json} introuvable.")
		with p.open("r", encoding="utf-8") as f:
			data = json.load(f)

		# Accepte plusieurs schémas pour rester tolérant aux variations de format.
		prescripts = None
		if isinstance(data, dict) and langue in data and isinstance(data[langue], dict) and "prescripts" in data[langue]:
			prescripts = data[langue]["prescripts"]
		elif isinstance(data, dict) and "prescripts" in data:
			prescripts = data["prescripts"]
		elif isinstance(data, list):
			prescripts = data
		else:
			raise KeyError(f"Langue {langue} ou clé 'prescripts' non trouvée dans {fichier_json}.")

		if not isinstance(prescripts, list):
			raise TypeError("La clé 'prescripts' doit contenir une liste de chaînes ou d'objets.")

		return cls(prescripts, langue)

	def list_texts(self) -> List[str]:
		"""Retourne uniquement le texte de chaque entrée."""
		return [it["text"] for it in self._items]

	def get_by_index(self, index: int) -> str:
		"""Récupère une entrée par index strict (lève IndexError si invalide)."""
		if index < 0 or index >= len(self._items):
			raise IndexError("Index prescript hors limites")
		return self._items[index]["text"]

	def get_by_id(self, idval: Any) -> Optional[str]:
		"""Récupère une entrée par identifiant logique (`id`) si présent."""
		for it in self._items:
			if it.get("id") == idval:
				return it["text"]
		return None

	def choose_random(self, seed: Optional[int] = None) -> str:
		"""Sélection aléatoire uniforme.

		`seed` permet un tirage reproductible localement (utile en test/debug).
		"""
		if seed is not None:
			rnd = random.Random(seed)
			return rnd.choice(self._items)["text"]
		return random.choice(self._items)["text"]

	def choose_weighted(self, seed: Optional[int] = None) -> str:
		"""Sélection aléatoire pondérée par `weight`.

		Poids négatifs forcés à 0. Si tous les poids valent 0, fallback en uniforme.
		"""
		weights = [max(0.0, float(it.get("weight", 1))) for it in self._items]
		if sum(weights) == 0:
			# Repli: si tous les poids sont nuls, repasser en distribution uniforme.
			weights = [1 for _ in self._items]
		if seed is not None:
			rnd = random.Random(seed)
			choice = rnd.choices(self._items, weights=weights, k=1)[0]
			return choice["text"]
		return random.choices(self._items, weights=weights, k=1)[0]["text"]

	def next_sequential(self) -> str:
		"""Sélection séquentielle circulaire (round-robin)."""
		if not self._items:
			raise IndexError("Aucun prescript disponible")
		val = self._items[self._seq_index % len(self._items)]["text"]
		self._seq_index += 1
		return val

	def format_text(self, text: str, context: Optional[Dict[str, Any]] = None) -> str:
		"""Applique `str.format(**context)` en mode tolérant.

		Si le format échoue (clé manquante, etc.), retourne le texte original.
		"""
		if not context:
			return text
		try:
			return text.format(**context)
		except Exception:
			# En cas d'échec de formatage, conserver le texte original.
			return text


def charger_prescripts(fichier_json: str = "data/prescript.json", langue: str = "fr") -> List[str]:
	"""Chargeur rétrocompatible qui retourne une liste de chaînes.

	Utiliser `PrescriptManager.load_from_file` pour les fonctionnalités avancées.
	"""
	# Wrapper historique conservé pour compatibilité avec l'ancien code.
	mgr = PrescriptManager.load_from_file(fichier_json, langue)
	return mgr.list_texts()

