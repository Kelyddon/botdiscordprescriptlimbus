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
