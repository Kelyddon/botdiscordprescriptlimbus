from typing import Optional

def espacer_texte(texte: str, espace: str = " ") -> str:
	return espace.join(list(texte))

def en_bloc_code(texte: str, lang: Optional[str] = None) -> str:
	if lang:
		return f"```{lang}\n{texte}\n```"
	return f"```\n{texte}\n```"

def styliser(texte: str, espace: str = " ", code_block: bool = True, lang: Optional[str] = None) -> str:
	t = espacer_texte(texte, espace) if espace else texte
	return en_bloc_code(t, lang) if code_block else t

def parse_color(s: Optional[str]) -> Optional['discord.Color']:
	"""Parse a color name or hex string and return a discord.Color or None.

	Accepts named colors: purple, red, green, blue, gold, orange, magenta, blurple.
	Accepts hex strings like `#RRGGBB` or `RRGGBB`.
	"""
	if not s:
		return None
	s = s.strip().lower()
	name_map = {
		'purple': None,  # filled at runtime to avoid circular import
		'red': None,
		'green': None,
		'blue': None,
		'gold': None,
		'orange': None,
		'magenta': None,
		'blurple': None,
	}
	try:
		import discord as _discord
		name_map['purple'] = _discord.Color.purple()
		name_map['red'] = _discord.Color.red()
		name_map['green'] = _discord.Color.green()
		name_map['blue'] = _discord.Color.blue()
		name_map['gold'] = _discord.Color.gold()
		name_map['orange'] = _discord.Color.orange()
		name_map['magenta'] = _discord.Color.magenta()
		name_map['blurple'] = _discord.Color.blurple()
	except Exception:
		return None


def espacer_unicode(texte: str, espace: str = '\u2002') -> str:
	"""Return text with unicode spaced characters between letters."""
	return espace.join(list(texte))


def glitch_text(texte: str, intensity: float = 0.06) -> str:
	"""Insert occasional diacritics/combining chars to simulate glitchy glyphs.

	intensity: fraction of characters to glitch (0..1)
	"""
	import random
	combs = ['\u0300', '\u0301', '\u0302', '\u0303', '\u0308', '\u0336']
	out = []
	for ch in texte:
		out.append(ch)
		if ch.strip() and random.random() < intensity:
			out.append(random.choice(combs))
	return ''.join(out)


def ascii_frame(texte: str, width: int = 60) -> str:
	"""Wrap text in a simple ASCII box preserving line breaks."""
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


def apply_prescript_style(texte: str, variant: Optional[str] = None) -> str:
	"""Apply a high-level prescript text style variant.

	Supported variants: None|'spaced'|'glitch'|'ascii'|'plain'
	"""
	if not variant:
		return texte
	v = variant.lower()
	if v == 'spaced':
		# use thin space for better visual
		return espacer_unicode(texte, '\u2009')
	if v == 'glitch':
		return glitch_text(texte, intensity=0.08)
	if v == 'ascii':
		return ascii_frame(texte)
	if v == 'plain':
		return texte
	# default fallback
	return texte

	if s in name_map:
		return name_map[s]
	if s.startswith('#'):
		s = s[1:]
	try:
		val = int(s, 16)
		import discord as _discord

		return _discord.Color(val)
	except Exception:
		return None
