import json
from pathlib import Path


def charger_prescripts(fichier_json: str = "data/prescript.json", langue: str = "fr"):
	"""Charge et retourne la liste de prescripts depuis un fichier JSON.

	Supporte deux formats JSON :
	- {"prescripts": [ ... ]}
	- {"fr": {"prescripts": [ ... ]}, ...}
	"""
	p = Path(fichier_json)
	if not p.exists():
		raise FileNotFoundError(f"Fichier {fichier_json} introuvable.")
	with p.open("r", encoding="utf-8") as f:
		data = json.load(f)

	if isinstance(data, dict) and langue in data and isinstance(data[langue], dict) and "prescripts" in data[langue]:
		prescripts = data[langue]["prescripts"]
	elif isinstance(data, dict) and "prescripts" in data:
		prescripts = data["prescripts"]
	else:
		raise KeyError(f"Langue {langue} ou clé 'prescripts' non trouvée dans {fichier_json}.")

	if not isinstance(prescripts, list):
		raise TypeError("La clé 'prescripts' doit contenir une liste de chaînes.")

	return prescripts
