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

    @discord.ui.button(label="Heads", style=discord.ButtonStyle.blurple)
    async def confirmer(
        self, button: discord.ui.Button, interaction: discord.Interaction
    ) -> None:
        self.valeur = "pile"
        self.stop()

    @discord.ui.button(label="Tails", style=discord.ButtonStyle.blurple)
    async def annuler(
        self, button: discord.ui.Button, interaction: discord.Interaction
    ) -> None:
        self.valeur = "face"
        self.stop()


class PierrePapierCiseaux(discord.ui.Select):
    def __init__(self) -> None:
        options = [
            discord.SelectOption(
                label="Scissors", description="You choose the scissors.", emoji="✂"
            ),
            discord.SelectOption(
                label="Rock", description="You choose the stone.", emoji="🪨"
            ),
            discord.SelectOption(
                label="Paper", description="You choose the paper.", emoji="🧻"
            ),
        ]
        super().__init__(
            placeholder="Choose...",
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
                f"**It's a tie!**\nYou have chosen {choix_utilisateur} "
                f"et j'ai choisi {choix_bot}."
            )
            embed_resultat.colour = 0xF59E42
        elif gagnant == 1:
            embed_resultat.description = (
                f"**You've won !**\nYou have chosen {choix_utilisateur} "
                f"and I chose {choix_bot}."
            )
            embed_resultat.colour = 0x9CDE7C
        else:
            embed_resultat.description = (
                f"**You've lost !**\nYou have chosen {choix_utilisateur} "
                f"and I chose {choix_bot}."
            )
            embed_resultat.colour = 0xE02B2B

        await interaction.response.edit_message(embed=embed_resultat, view=None)


class Fun(commands.Cog, name="fun"):
    def __init__(self, bot) -> None:
        self.bot = bot

    @commands.hybrid_command(
        name="coinfilp",
        description="Flip a coin.",
    )
    async def coinflip(self, context: Context) -> None:
        """
        Lancer une pièce pour obtenir pile ou face.
        """
        view = Choix()
        await context.send("Flip a coin :", view=view)
        await view.wait()

        choix_utilisateur = view.valeur
        choix_bot = random.choice(["pile", "face"])

        if choix_utilisateur == choix_bot:
            await context.send(f"Its {choix_bot} ! You've won !")
        else:
            await context.send(f"Its {choix_bot} ! You've lost !")

async def setup(bot):
    await bot.add_cog(Fun(bot))