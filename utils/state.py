import asyncio

class PrescriptState:
	def __init__(self):
		self.paused = asyncio.Event()
		self.paused.set()
		self.stopped = False

	async def pause(self):
		self.paused.clear()

	async def resume(self):
		self.paused.set()

	async def stop(self):
		self.stopped = True
		# make sure waiters are released
		self.paused.set()

	async def wait_if_paused(self):
		await self.paused.wait()

	def reset(self):
		self.paused.set()
		self.stopped = False
