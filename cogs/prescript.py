import discord
from discord.ext import commands
import asyncio
import random
from typing import Optional
import io
from utils.renderer import render_text_image
from utils.text_manager import charger_prescripts
from utils.style import styliser, parse_color
from utils.state import PrescriptState

PAUSES_SPECIFIQUES = {'.': 0.5, ',': 0.25, '!': 0.6, '?': 0.6, '\n': 0.4, '…': 0.8, '-': 0.12}


def _parse_color(s: Optional[str]) -> Optional[discord.Color]:
    if not s:
        return None
    s = s.strip().lower()
    name_map = {
        'purple': discord.Color.purple(),
        'red': discord.Color.red(),
        'green': discord.Color.green(),
        'blue': discord.Color.blue(),
        'gold': discord.Color.gold(),
        'orange': discord.Color.orange(),
        'magenta': discord.Color.magenta(),
        'blurple': discord.Color.blurple(),
    }
    if s in name_map:
        return name_map[s]
    # accept hex like #RRGGBB or RRGGBB
    if s.startswith('#'):
        s = s[1:]
    try:
        val = int(s, 16)
        return discord.Color(val)
    except Exception:
        return None


class PrescriptCog(commands.Cog):
    """Cog pour générer et afficher des prescripts avec un effet "machine à écrire".
    Gère un état par canal et permet pause/resume/stop. Fournit des commandes hybrides (préfixe + slash).
    """

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.states: dict[int, PrescriptState] = {}
        self.tasks: dict[int, asyncio.Task] = {}

    def get_state(self, channel_id: int) -> PrescriptState:
        st = self.states.get(channel_id)
        if st is None:
            st = PrescriptState()
            self.states[channel_id] = st
        return st

    @commands.hybrid_command(name='prescript', with_app_command=True, description='Génère un prescript (option embed)')
    async def prescript(self, ctx: commands.Context, index: Optional[int] = None, embed: Optional[bool] = False, embed_color: Optional[str] = None, title: Optional[str] = None, image: Optional[bool] = False, style: Optional[str] = None):
        """Lance l'affichage d'un prescript. Optionnel: `index` pour sélectionner une phrase, `embed` pour utiliser un embed, `embed_color` en hex ou nom, `title` pour changer le titre."""
        prescripts = charger_prescripts("data/prescript.json", "fr")
        if index is not None:
            if 0 <= index < len(prescripts):
                texte = prescripts[index]
            else:
                await ctx.reply("Index hors limites.")
                return
        else:
            texte = random.choice(prescripts)

        state = self.get_state(ctx.channel.id)

        # apply textual style variants (spaced, glitch, ascii, plain)
        try:
            from utils.style import apply_prescript_style
            texte = apply_prescript_style(texte, style)
        except Exception:
            pass

        existing = self.tasks.get(ctx.channel.id)
        if existing and not existing.done():
            await ctx.reply("Un prescript est déjà en cours dans ce canal. Utilisez /stop_prescript pour l'arrêter.")
            return

        # render as image (final snapshot) if requested
        if image:
            try:
                png = await render_text_image(texte, bg_color='#0b0b0b', text_color='#eaeaea')
            except RuntimeError as e:
                await ctx.reply(f"Renderer unavailable: {e}")
                return
            fp = io.BytesIO(png)
            fp.seek(0)
            await ctx.reply(file=discord.File(fp, filename="prescript.png"))
            return

        # envoi initial for progressive text
        if embed:
            color = parse_color(embed_color) or discord.Color.purple()
            embed_obj = discord.Embed(title=title or "Prescript", description="", color=color)
            message = await ctx.reply(embed=embed_obj)
            mode = 'embed'
        else:
            message = await ctx.reply(styliser("", espace=" ", code_block=True))
            mode = 'code'

        task = asyncio.create_task(self._display_progressive(message, texte, state, mode=mode, embed_title=title, embed_color=embed_color))
        self.tasks[ctx.channel.id] = task

    async def _display_progressive(self, message: discord.Message, texte: str, state: PrescriptState, delai_base: float = 0.04, chunk_size: int = 6, mode: str = 'code', embed_title: Optional[str] = None, embed_color: Optional[str] = None):
        affichage = ""
        buffer = ""
        total = len(texte)
        try:
            for ch in texte:
                await state.wait_if_paused()
                if state.stopped:
                    break
                buffer += ch

                pause = PAUSES_SPECIFIQUES.get(ch)
                if pause is not None or len(buffer) >= chunk_size:
                    affichage += buffer
                    buffer = ""
                    try:
                        if mode == 'embed':
                            color = parse_color(embed_color) or discord.Color.purple()
                            embed = discord.Embed(title=embed_title or "Prescript", description=affichage, color=color)
                            shown = len(affichage)
                            pct = shown / max(1, total) * 100
                            embed.set_footer(text=f"{shown}/{total} ({pct:.0f}%)")
                            await message.edit(embed=embed)
                        else:
                            await message.edit(content=styliser(affichage, espace=" ", code_block=True))
                    except Exception:
                        pass
                    if pause:
                        await asyncio.sleep(pause)
                    else:
                        await asyncio.sleep(delai_base * min(chunk_size, max(1, len(affichage))))

            # flush
            if buffer and not state.stopped:
                affichage += buffer
                try:
                    if mode == 'embed':
                        color = parse_color(embed_color) or discord.Color.purple()
                        embed = discord.Embed(title=embed_title or "Prescript", description=affichage, color=color)
                        shown = len(affichage)
                        pct = shown / max(1, total) * 100
                        embed.set_footer(text=f"{shown}/{total} ({pct:.0f}%)")
                        await message.edit(embed=embed)
                    else:
                        await message.edit(content=styliser(affichage, espace=" ", code_block=True))
                except Exception:
                    pass

        finally:
            state.reset()
            return

    @commands.hybrid_command(name='pause_prescript', with_app_command=True, description='Met en pause l affichage en cours')
    async def pause_prescript(self, ctx: commands.Context):
        st = self.get_state(ctx.channel.id)
        await st.pause()
        await ctx.reply("Affichage en pause.")

    @commands.hybrid_command(name='resume_prescript', with_app_command=True, description='Reprend un affichage mis en pause')
    async def resume_prescript(self, ctx: commands.Context):
        st = self.get_state(ctx.channel.id)
        await st.resume()
        await ctx.reply("Affichage repris.")

    @commands.hybrid_command(name='stop_prescript', with_app_command=True, description='Arrête l affichage en cours')
    async def stop_prescript(self, ctx: commands.Context):
        st = self.get_state(ctx.channel.id)
        await st.stop()
        task = self.tasks.get(ctx.channel.id)
        if task and not task.done():
            task.cancel()
        await ctx.reply("Affichage arrêté.")


async def setup(bot: commands.Bot):
    await bot.add_cog(PrescriptCog(bot))
def main():
    print("Hello from botindexprescripte!")


if __name__ == "__main__":
    main()
