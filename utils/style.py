"""Utilitaires de style/formatage pour l'affichage Discord.

Ce module isole les transformations visuelles (espacement, boîte ASCII,
effet glitch) et les helpers de découpage pour édition progressive.
"""

from typing import Optional, List
import textwrap


def espacer_texte(texte: str, espace: str = " ") -> str:
	"""Insère `espace` entre tous les caractères d'un texte."""
	return espace.join(list(texte))


def en_bloc_code(texte: str, lang: Optional[str] = None) -> str:
	"""Encapsule le texte dans un bloc Markdown triple backtick.

	Si `lang` est fourni, active la variante ```lang pour la coloration.
	"""
	if lang:
		return f"```{lang}\n{texte}\n```"
	return f"```\n{texte}\n```"


def styliser(texte: str, espace: str = " ", code_block: bool = True, lang: Optional[str] = None) -> str:
	"""Pipeline compact: espacement optionnel + bloc code optionnel."""
	t = espacer_texte(texte, espace) if espace else texte
	return en_bloc_code(t, lang) if code_block else t


def parse_color(s: Optional[str]) -> Optional['discord.Color']:
	"""Analyse un nom de couleur ou une chaîne hexadécimale.

	Accepte les noms: purple, red, green, blue, gold, orange, magenta, blurple.
	Accepte aussi les formats `#RRGGBB` ou `RRGGBB`.
	"""
	if not s:
		return None
	# Normalisation entrée utilisateur (espaces/casse)
	s = s.strip().lower()
	try:
		import discord as _discord
	except Exception:
		return None

	name_map = {
		'purple': _discord.Color.purple(),
		'red': _discord.Color.red(),
		'green': _discord.Color.green(),
		'blue': _discord.Color.blue(),
		'gold': _discord.Color.gold(),
		'orange': _discord.Color.orange(),
		'magenta': _discord.Color.magenta(),
		'blurple': _discord.Color.blurple(),
	}

	if s in name_map:
		return name_map[s]
	# Support de #RRGGBB et RRGGBB
	if s.startswith('#'):
		s = s[1:]
	try:
		val = int(s, 16)
		return _discord.Color(val)
	except Exception:
		return None


def espacer_unicode(texte: str, espace: str = '\u2002') -> str:
	"""Retourne le texte avec un espace Unicode entre chaque caractère."""
	return espace.join(list(texte))


def glitch_text(texte: str, intensity: float = 0.06) -> str:
	"""Insère ponctuellement des caractères combinés pour un effet glitch.

	`intensity`: fraction des caractères affectés (0..1)
	"""
	import random
	# Combinaisons unicode ajoutées derrière certains caractères pour effet "glitch"
	combs = ['\u0300', '\u0301', '\u0302', '\u0303', '\u0308', '\u0336']
	out = []
	for ch in texte:
		out.append(ch)
		if ch.strip() and random.random() < intensity:
			out.append(random.choice(combs))
	return ''.join(out)


def ascii_frame(texte: str, width: int = 60) -> str:
	"""Encadre le texte dans une boîte ASCII simple en conservant les sauts de ligne."""
	# Découpe manuelle en lignes de largeur fixe, puis insertion dans un cadre ASCII.
	lines = []
	for paragraph in texte.split('\n'):
		while paragraph:
			lines.append(paragraph[:width])
			paragraph = paragraph[width:]
		if not paragraph and texte.endswith('\n'):
			lines.append('')
	maxw = max((len(l) for l in lines), default=0)
	top = '+' + '-' * (maxw + 2) + '+'
	middle = '\n'.join('| ' + l.ljust(maxw) + ' |' for l in lines)
	return f"{top}\n{middle}\n{top}"


def chunk_text_for_edits(text: str, chunk_size: int = 4, prefer_word_boundary: bool = True) -> List[str]:
	"""Découpe le texte en morceaux adaptés à une édition progressive.

	- `chunk_size`: longueur maximale d'un morceau.
	- `prefer_word_boundary`: évite autant que possible de couper au milieu d'un mot.
	"""
	if chunk_size <= 0:
		return [text]
	# Découpage incrémental: utile pour simuler une écriture progressive.
	chunks: List[str] = []
	i = 0
	n = len(text)
	while i < n:
		end = min(i + chunk_size, n)
		if prefer_word_boundary and end < n and not text[end].isspace():
			# Tente d'éviter de couper un mot au milieu.
			last_space = text.rfind(' ', i, end)
			if last_space != -1 and last_space + 1 > i:
				end = last_space + 1
		chunks.append(text[i:end])
		i = end
	return chunks


def prepare_text_for_discord_edit(texte: str, *, variant: Optional[str] = None, space_char: str = '\u2009',
								  glitch_intensity: float = 0.08, ascii_width: int = 60,
								  chunk_size: int = 4, prefer_word_boundary: bool = True) -> List[str]:
	"""Applique un style puis retourne des morceaux pour édition progressive.

	La liste retournée est prévue pour mettre à jour séquentiellement un message Discord.
	"""
	# 1) Appliquer le style (spaced/glitch/ascii/plain)
	styled = apply_prescript_style(texte, variant=variant, space_char=space_char,
								   glitch_intensity=glitch_intensity, ascii_width=ascii_width)
	# 2) Le transformer en chunks de progression pour les `message.edit(...)`
	return chunk_text_for_edits(styled, chunk_size=chunk_size, prefer_word_boundary=prefer_word_boundary)


def apply_prescript_style(texte: str, variant: Optional[str] = None, *,
						  space_char: str = '\u2009', glitch_intensity: float = 0.08,
						  ascii_width: int = 60) -> str:
	"""Applique une variante de style de haut niveau au texte du prescript.

	Variantes supportées: None|'spaced'|'glitch'|'ascii'|'plain'.
	Les paramètres supplémentaires permettent d'ajuster le rendu sans changer la logique appelante.
	"""
	if not variant:
		# Pas de style demandé => texte brut
		return texte
	v = variant.lower()
	if v == 'spaced':
		# Espacement typographique (unicode thin space ou équivalent)
		return espacer_unicode(texte, space_char)
	if v == 'glitch':
		# Effet volontairement bruité (désactivé en mode aléatoire dans le cog)
		return glitch_text(texte, intensity=glitch_intensity)
	if v == 'ascii':
		# Encadrement en boîte monospaced
		return ascii_frame(texte, width=ascii_width)
	if v == 'plain':
		return texte
	# Repli par défaut
	return texte
