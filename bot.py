"""Point d'entrée du bot Discord Prescript.

Responsabilités:
- lire la configuration CLI / variables d'environnement,
- initialiser l'instance `commands.Bot`,
- charger les extensions/cogs,
- lancer la session Discord.
"""

import os
import asyncio
import argparse
import logging
try:
	from dotenv import load_dotenv
	_have_dotenv = True
except Exception:
	_have_dotenv = False
import discord
from discord.ext import commands

if _have_dotenv:
	try:
		# Charge automatiquement `.env` si disponible.
		load_dotenv()
	except Exception:
		pass

logger = logging.getLogger(__name__)


def parse_args():
	"""Construit et analyse les arguments CLI du bot."""
	p = argparse.ArgumentParser(description='Run the prescript Discord bot (dev-friendly)')
	p.add_argument('-t', '--token', help='Discord bot token (overrides DISCORD_TOKEN env var)')
	p.add_argument('--dev-guild', help='Guild ID to register app commands to during development', type=int)
	p.add_argument('--no-sync', help='Do not sync application commands on startup', action='store_true')
	p.add_argument('--debug', help='Enable debug logging', action='store_true')
	return p.parse_args()


async def start_bot(token: str, dev_guild: int | None = None, do_sync: bool = True) -> None:
	"""Initialise et démarre le bot.

	- `dev_guild`: accélère la synchro des slash commands sur une guilde de test.
	- `do_sync`: permet de désactiver explicitement la synchronisation au startup.
	"""
	intents = discord.Intents.default()
	# Nécessaire pour les commandes préfixées qui lisent le contenu texte.
	intents.message_content = True

	bot = commands.Bot(command_prefix='!', intents=intents)

	@bot.event
	async def on_ready():
		# Callback Discord déclenché quand la connexion Gateway est prête.
		logger.info('Logged in as %s (id=%s)', bot.user, bot.user.id)
		print(f'Logged in as {bot.user} (id={bot.user.id})')
		if dev_guild:
			print(f'Using dev guild id: {dev_guild} — commands will be registered there for faster updates')

	# Commande de test rapide pour vérifier la réactivité du bot.
	@bot.command(name='ping')
	async def _ping(ctx: commands.Context):
		# Commande utilitaire minimale pour vérifier la santé du bot.
		await ctx.reply('pong')

	async with bot:
		# 1) Chargement des cogs/extensions.
		try:
			await bot.load_extension('cogs.prescript')
		except Exception as e:
			logger.exception('Failed loading cogs: %s', e)
		# 2) Synchronisation des slash commands (globale ou guild-specific).
		if do_sync:
			try:
				if dev_guild:
					await bot.tree.sync(guild=discord.Object(id=dev_guild))
				else:
					await bot.tree.sync()
			except Exception:
				logger.exception('Command sync failed; continuing')
		# 3) Démarrage effectif de la session Discord.
		await bot.start(token)


if __name__ == '__main__':
	# Niveau de logs configurable depuis la CLI.
	args = parse_args()
	if args.debug:
		logging.basicConfig(level=logging.DEBUG)
	else:
		logging.basicConfig(level=logging.INFO)

	token = args.token or os.getenv('DISCORD_TOKEN')
	if not token:
		# Message explicite pour éviter un démarrage silencieusement invalide.
		print('DISCORD_TOKEN not set. You may pass --token your_token or set DISCORD_TOKEN in the environment.')
		raise SystemExit(1)

	try:
		asyncio.run(start_bot(token, dev_guild=args.dev_guild, do_sync=not args.no_sync))
	except KeyboardInterrupt:
		# Arrêt propre au CTRL+C.
		print('Interrupted — shutting down.')
