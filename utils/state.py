"""État d'exécution d'un prescript pour un canal Discord.

L'objet encapsule:
- une pause coopérative (`asyncio.Event`),
- un drapeau d'arrêt,
- des primitives simples utilisées par la boucle d'affichage progressif.
"""

import asyncio

class PrescriptState:
	def __init__(self):
		# `paused` est "set" quand l'exécution est autorisée.
		self.paused = asyncio.Event()
		self.paused.set()
		# `stopped` force l'arrêt de la boucle de rendu.
		self.stopped = False

	async def pause(self):
		"""Met l'exécution en pause (les waiters bloquent)."""
		self.paused.clear()

	async def resume(self):
		"""Reprend l'exécution après une pause."""
		self.paused.set()

	async def stop(self):
		"""Demande l'arrêt définitif de la tâche courante."""
		self.stopped = True
		# make sure waiters are released
		self.paused.set()

	async def wait_if_paused(self):
		"""Attend tant que l'état est en pause."""
		await self.paused.wait()

	def reset(self):
		"""Remet l'état initial pour une prochaine exécution."""
		self.paused.set()
		self.stopped = False
