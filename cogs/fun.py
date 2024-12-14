"""
Copyright © Krypton 2019-Présent - https://github.com/kkrypt0nn (https://krypton.ninja)
Description:
🐍 Un modèle simple pour commencer à coder votre propre bot Discord personnalisé en Python

Version : 6.2.0
"""

import random

import aiohttp
import discord
from discord.ext import commands
from discord.ext.commands import Context


class Choix(discord.ui.View):
    def __init__(self) -> None:
        super().__init__()
        self.valeur = None

    @discord.ui.button(label="Pile", style=discord.ButtonStyle.blurple)
    async def confirmer(
        self, button: discord.ui.Button, interaction: discord.Interaction
    ) -> None:
        self.valeur = "pile"
        self.stop()

    @discord.ui.button(label="Face", style=discord.ButtonStyle.blurple)
    async def annuler(
        self, button: discord.ui.Button, interaction: discord.Interaction
    ) -> None:
        self.valeur = "face"
        self.stop()


class PierrePapierCiseaux(discord.ui.Select):
    def __init__(self) -> None:
        options = [
            discord.SelectOption(
                label="Ciseaux", description="Vous choisissez les ciseaux.", emoji="✂"
            ),
            discord.SelectOption(
                label="Pierre", description="Vous choisissez la pierre.", emoji="🪨"
            ),
            discord.SelectOption(
                label="Papier", description="Vous choisissez le papier.", emoji="🧻"
            ),
        ]
        super().__init__(
            placeholder="Choisissez...",
            min_values=1,
            max_values=1,
            options=options,
        )

    async def callback(self, interaction: discord.Interaction) -> None:
        choix = {
            "pierre": 0,
            "papier": 1,
            "ciseaux": 2,
        }
        choix_utilisateur = self.values[0].lower()
        index_choix_utilisateur = choix[choix_utilisateur]

        choix_bot = random.choice(list(choix.keys()))
        index_choix_bot = choix[choix_bot]

        embed_resultat = discord.Embed(color=0xBEBEFE)
        embed_resultat.set_author(
            name=interaction.user.name, icon_url=interaction.user.display_avatar.url
        )

        gagnant = (3 + index_choix_utilisateur - index_choix_bot) % 3
        if gagnant == 0:
            embed_resultat.description = (
                f"**C'est une égalité !**\nVous avez choisi {choix_utilisateur} "
                f"et j'ai choisi {choix_bot}."
            )
            embed_resultat.colour = 0xF59E42
        elif gagnant == 1:
            embed_resultat.description = (
                f"**Vous avez gagné !**\nVous avez choisi {choix_utilisateur} "
                f"et j'ai choisi {choix_bot}."
            )
            embed_resultat.colour = 0x9CDE7C
        else:
            embed_resultat.description = (
                f"**Vous avez perdu !**\nVous avez choisi {choix_utilisateur} "
                f"et j'ai choisi {choix_bot}."
            )
            embed_resultat.colour = 0xE02B2B

        await interaction.response.edit_message(embed=embed_resultat, view=None)


class Fun(commands.Cog, name="fun"):
    def __init__(self, bot) -> None:
        self.bot = bot

    @commands.hybrid_command(
        name="pileouface",
        description="Lancer une pièce.",
    )
    async def coinflip(self, context: Context) -> None:
        """
        Lancer une pièce pour obtenir pile ou face.
        """
        view = Choix()
        await context.send("Choisissez pile ou face :", view=view)
        await view.wait()

        choix_utilisateur = view.valeur
        choix_bot = random.choice(["pile", "face"])

        if choix_utilisateur == choix_bot:
            await context.send(f"C'est {choix_bot} ! Vous avez gagné !")
        else:
            await context.send(f"C'est {choix_bot} ! Vous avez perdu !")

    @commands.hybrid_command(
        name="pierrepapierciseaux",
        description="Jouez à Pierre-Papier-Ciseaux.",
    )
    async def play_rps(self, context: Context) -> None:
        """
        Jouez à Pierre-Papier-Ciseaux contre le bot.
        """
        view = discord.ui.View()
        select = PierrePapierCiseaux()
        view.add_item(select)
        await context.send("Choisissez votre option :", view=view)


async def setup(bot):
    await bot.add_cog(Fun(bot))