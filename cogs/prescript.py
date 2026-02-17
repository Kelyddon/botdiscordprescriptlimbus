"""Gestionnaire Discord des prescripts.

Ce module gère:
- la sélection d'un prescript (liste JSON ou générateur procédural),
- l'application de style visuel,
- l'affichage progressif (typewriter),
- les commandes de contrôle pause/reprise/arrêt.

La logique métier de génération reste dans `utils.prescript_generator`.
Ici, on orchestre surtout l'I/O Discord et l'UX d'affichage.
"""

import discord
from discord.ext import commands
import asyncio
import random
from typing import Optional
import io
from utils.renderer import render_text_image
from utils.text_manager import PrescriptManager
from utils.prescript_generator import generate_prescript
from utils.style import en_bloc_code, parse_color, apply_prescript_style
from utils.state import PrescriptState

PAUSES_SPECIFIQUES = {'.': 0.5, ',': 0.25, '!': 0.6, '?': 0.6, '\n': 0.4, '…': 0.8, '-': 0.12}


def _is_ascii_box(text: str) -> bool:
    """Détecte si un texte ressemble à une boîte ASCII.

    On utilise ce test pour appliquer un rendu progressif spécial:
    afficher immédiatement la bordure puis révéler le contenu interne.
    """
    lines = text.split('\n')
    if len(lines) < 3:
        return False
    top = lines[0]
    bottom = lines[-1]
    if not (top.startswith('+') and top.endswith('+') and bottom.startswith('+') and bottom.endswith('+')):
        return False
    return True


def _ascii_box_initial_and_reveal_positions(text: str) -> tuple[str, list[int]]:
    """Prépare une version "frame visible" + positions à révéler.

    Retourne:
    - le texte initial où les caractères internes sont masqués par des espaces,
    - la liste des indices de caractères à révéler progressivement.
    """
    target_chars = list(text)
    current_chars = target_chars.copy()
    reveal_positions: list[int] = []

    lines = text.split('\n')
    cursor = 0
    for line_index, line in enumerate(lines):
        is_border_line = line_index == 0 or line_index == len(lines) - 1
        for col, ch in enumerate(line):
            absolute_index = cursor + col
            if is_border_line:
                continue
            if col == 0 or col == len(line) - 1:
                continue
            if ch != ' ':
                current_chars[absolute_index] = ' '
                reveal_positions.append(absolute_index)
        cursor += len(line)
        if line_index < len(lines) - 1:
            cursor += 1

    return ''.join(current_chars), reveal_positions


class PrescriptCog(commands.Cog):
    """Cog pour générer et afficher des prescripts avec un effet "machine à écrire".
    Gère un état par canal et permet pause/resume/stop. Fournit des commandes hybrides (préfixe + slash).
    """

    def __init__(self, bot: commands.Bot):
        # `states`: état de pause/stop par canal
        # `tasks`: tâche asyncio d'affichage progressif par canal
        self.bot = bot
        self.states: dict[int, PrescriptState] = {}
        self.tasks: dict[int, asyncio.Task] = {}

    def get_state(self, channel_id: int) -> PrescriptState:
        """Récupère (ou crée) l'état d'exécution associé à un canal."""
        st = self.states.get(channel_id)
        if st is None:
            st = PrescriptState()
            self.states[channel_id] = st
        return st

    async def _select_prescript_text(self, ctx: commands.Context, mgr: PrescriptManager, index: Optional[int]) -> Optional[str]:
        """Sélectionne le texte source du prescript.

        Priorités:
        1) `index` explicite si fourni,
        2) générateur procédural pour l'anglais,
        3) fallback sur liste (aléatoire/pondéré/séquentiel).

        Retourne `None` si l'index demandé est invalide (réponse envoyée à l'utilisateur).
        """
        if index is not None:
            try:
                return mgr.get_by_index(int(index))
            except Exception:
                await ctx.reply("Index hors limites.")
                return None

        if mgr and mgr.language == 'en':
            rng = lambda: random.random()
            try:
                return generate_prescript(rng)
            except Exception:
                return mgr.choose_random()

        pick_mode = random.choices(['weighted', 'random', 'sequential'], weights=[0.2, 0.6, 0.2], k=1)[0]
        if pick_mode == 'weighted':
            return mgr.choose_weighted()
        if pick_mode == 'sequential':
            return mgr.next_sequential()
        return mgr.choose_random()

    def _select_style(self, style: Optional[str]) -> str:
        """Choisit un style de rendu.

        - Si l'utilisateur fournit un style, on le respecte.
        - Sinon, on choisit aléatoirement parmi des styles lisibles.
        """
        if style:
            return style
        return random.choices(['spaced', 'plain', 'ascii'], weights=[0.5, 0.4, 0.1], k=1)[0]

    def _make_embed(self, description: str, total: int, title: Optional[str], embed_color: Optional[str]) -> discord.Embed:
        """Construit l'embed avec barre de progression textuelle.

        Le footer affiche `caractères_affichés / total` pour suivre l'avancement
        pendant l'effet machine à écrire.
        """
        color = parse_color(embed_color) or discord.Color.purple()
        embed_obj = discord.Embed(title=title or "Prescript", description=description, color=color)
        shown = len(description)
        pct = shown / max(1, total) * 100
        embed_obj.set_footer(text=f"{shown}/{total} ({pct:.0f}%)")
        return embed_obj

    async def _send_initial_message(self, ctx: commands.Context, use_embed: bool, title: Optional[str], embed_color: Optional[str]) -> tuple[discord.Message, str]:
        """Envoie le message de départ et retourne `(message, mode)`.

        `mode` vaut:
        - `'embed'` si affichage embed,
        - `'code'` si affichage dans un bloc de code.
        """
        if use_embed:
            embed_obj = self._make_embed("", 1, title, embed_color)
            message = await ctx.reply(embed=embed_obj)
            return message, 'embed'
        message = await ctx.reply(en_bloc_code(""))
        return message, 'code'

    async def _edit_progress_message(self, message: discord.Message, mode: str, content: str, total: int, embed_title: Optional[str], embed_color: Optional[str]) -> None:
        """Met à jour le message courant selon le mode d'affichage."""
        if mode == 'embed':
            await message.edit(embed=self._make_embed(content, total, embed_title, embed_color))
        else:
            await message.edit(content=en_bloc_code(content))

    @commands.hybrid_command(name='prescript', with_app_command=True, description='Génère un prescript (option embed)')
    async def prescript(self, ctx: commands.Context, index: Optional[int] = None, embed: Optional[bool] = False, embed_color: Optional[str] = None, title: Optional[str] = None, image: Optional[bool] = False, style: Optional[str] = None):
        """Lance l'affichage d'un prescript. Optionnel: `index` pour sélectionner une phrase, `embed` pour utiliser un embed, `embed_color` en hex ou nom, `title` pour changer le titre."""
        # 1) Charger la source de prescripts (langue anglaise pour la logique actuelle)
        lang = 'en'
        mgr = PrescriptManager.load_from_file("data/prescript.json", lang)

        # 2) Choisir le texte final à afficher
        texte = await self._select_prescript_text(ctx, mgr, index)
        if texte is None:
            return

        state = self.get_state(ctx.channel.id)

        # 3) Appliquer le style visuel de sortie
        style = self._select_style(style)
        try:
            texte = apply_prescript_style(texte, style)
        except Exception:
            pass

        # 4) Protéger le canal: un seul affichage progressif à la fois
        existing = self.tasks.get(ctx.channel.id)
        if existing and not existing.done():
            await ctx.reply("Un prescript est déjà en cours dans ce canal. Utilisez /stop_prescript pour l'arrêter.")
            return

        # 5) Option image: rendu direct et sortie immédiate (pas de progression texte)
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

        # 6) Envoyer le message vide, puis lancer la tâche de révélation progressive
        message, mode = await self._send_initial_message(ctx, bool(embed), title, embed_color)

        chunk = random.randint(3, 8)
        base_delay = random.uniform(0.03, 0.08)
        task = asyncio.create_task(self._display_progressive(message, texte, state, delai_base=base_delay, chunk_size=chunk, mode=mode, embed_title=title, embed_color=embed_color))
        self.tasks[ctx.channel.id] = task

    async def _display_progressive(self, message: discord.Message, texte: str, state: PrescriptState, delai_base: float = 0.04, chunk_size: int = 6, mode: str = 'code', embed_title: Optional[str] = None, embed_color: Optional[str] = None):
        """Anime l'apparition progressive du prescript.

        Deux chemins:
        - Boîte ASCII: la bordure est affichée immédiatement, puis le texte interne est révélé.
        - Texte standard: accumulation par buffer et flush selon ponctuation/taille de chunk.
        """
        affichage = ""
        buffer = ""
        total = len(texte)
        try:
            # Chemin spécial ASCII pour conserver la lisibilité de la bordure.
            if mode == 'code' and _is_ascii_box(texte):
                initial, reveal_positions = _ascii_box_initial_and_reveal_positions(texte)
                target_chars = list(texte)
                current_chars = list(initial)

                try:
                    await message.edit(content=en_bloc_code(initial))
                except Exception:
                    pass

                pending = 0
                for pos in reveal_positions:
                    # Gestion pause/stop canal par canal.
                    await state.wait_if_paused()
                    if state.stopped:
                        break

                    ch = target_chars[pos]
                    current_chars[pos] = ch
                    pending += 1

                    pause = PAUSES_SPECIFIQUES.get(ch)
                    # Flush dès ponctuation forte ou chunk plein.
                    if pause is not None or pending >= chunk_size:
                        try:
                            await self._edit_progress_message(message, mode, ''.join(current_chars), total, embed_title, embed_color)
                        except Exception:
                            pass
                        pending = 0
                        if pause:
                            await asyncio.sleep(pause)
                        else:
                            await asyncio.sleep(delai_base * max(1, chunk_size))

                if pending and not state.stopped:
                    try:
                        await self._edit_progress_message(message, mode, ''.join(current_chars), total, embed_title, embed_color)
                    except Exception:
                        pass

                return

            # Chemin standard: écrit le texte caractère par caractère.
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
                        await self._edit_progress_message(message, mode, affichage, total, embed_title, embed_color)
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
                    await self._edit_progress_message(message, mode, affichage, total, embed_title, embed_color)
                except Exception:
                    pass

        finally:
            # Toujours remettre l'état au propre même en cas d'erreur/cancel.
            state.reset()
            return

    @commands.hybrid_command(name='pause_prescript', with_app_command=True, description='Met en pause l affichage en cours')
    async def pause_prescript(self, ctx: commands.Context):
        """Met en pause l'animation active dans le canal courant."""
        st = self.get_state(ctx.channel.id)
        await st.pause()
        await ctx.reply("Affichage en pause.")

    @commands.hybrid_command(name='resume_prescript', with_app_command=True, description='Reprend un affichage mis en pause')
    async def resume_prescript(self, ctx: commands.Context):
        """Relance une animation précédemment mise en pause."""
        st = self.get_state(ctx.channel.id)
        await st.resume()
        await ctx.reply("Affichage repris.")

    @commands.hybrid_command(name='stop_prescript', with_app_command=True, description='Arrête l affichage en cours')
    async def stop_prescript(self, ctx: commands.Context):
        """Arrête complètement la tâche d'affichage du canal courant."""
        st = self.get_state(ctx.channel.id)
        await st.stop()
        task = self.tasks.get(ctx.channel.id)
        if task and not task.done():
            task.cancel()
        await ctx.reply("Affichage arrêté.")


async def setup(bot: commands.Bot):
    await bot.add_cog(PrescriptCog(bot))
