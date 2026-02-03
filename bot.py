import os
import asyncio
try:
	from dotenv import load_dotenv
	_have_dotenv = True
except Exception:
	_have_dotenv = False
import discord
from discord.ext import commands

if _have_dotenv:
	try:
		load_dotenv()
	except Exception:
		pass

TOKEN = os.getenv("DISCORD_TOKEN")
if not TOKEN:
	print("DISCORD_TOKEN not set. Please set it as an environment variable or in a .env file.")
	raise SystemExit(1)

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)


async def main() -> None:
	async with bot:
		# charge le cog prescript
		await bot.load_extension("cogs.prescript")
		# synchronise les commandes d'application (slash) après avoir chargé les cogs
		try:
			await bot.tree.sync()
		except Exception:
			pass
		await bot.start(TOKEN)


if __name__ == "__main__":
	asyncio.run(main())
