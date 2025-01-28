"""
Copyright © Krypton 2019-Présent - https://github.com/kkrypt0nn (https://krypton.ninja)
Description:
🐍 Un modèle simple pour commencer à coder votre propre bot Discord personnalisé en Python

Version : 6.2.0
"""

import discord
from discord import app_commands
from discord.ext import commands
from discord.ext.commands import Context
from typing import Optional


class Owner(commands.Cog, name="propriétaire"):
    def __init__(self, bot) -> None:
        self.bot = bot

    @commands.command(
        name="sync",
        description="Synchronise les commandes slash.",
    )
    @app_commands.describe(scope="Le champ de la synchronisation. Peut être `global` ou `guild`")
    @commands.is_owner()
    async def sync(self, context: Context, scope: str) -> None:
        """
        Synchronise les commandes slash.

        :param context: Le contexte de la commande.
        :param scope: Le champ de la synchronisation. Peut être `global` ou `guild`.
        """

        if scope == "global":
            await context.bot.tree.sync()
            embed = discord.Embed(
                description="Les commandes slash ont été synchronisées globalement.",
                color=0xBEBEFE,
            )
            await context.send(embed=embed)
            return
        elif scope == "guild":
            context.bot.tree.copy_global_to(guild=context.guild)
            await context.bot.tree.sync(guild=context.guild)
            embed = discord.Embed(
                description="Les commandes slash ont été synchronisées dans ce serveur.",
                color=0xBEBEFE,
            )
            await context.send(embed=embed)
            return
        embed = discord.Embed(
            description="Le champ doit être `global` ou `guild`.", color=0xE02B2B
        )
        await context.send(embed=embed)

    @commands.command(
        name="unsync",
        description="Désynchronise les commandes slash.",
    )
    @app_commands.describe(
        scope="Le champ de la synchronisation. Peut être `global`, `current_guild` ou `guild`"
    )
    @commands.is_owner()
    async def unsync(self, context: Context, scope: str) -> None:
        """
        Désynchronise les commandes slash.

        :param context: Le contexte de la commande.
        :param scope: Le champ de la synchronisation. Peut être `global`, `current_guild` ou `guild`.
        """

        if scope == "global":
            context.bot.tree.clear_commands(guild=None)
            await context.bot.tree.sync()
            embed = discord.Embed(
                description="Les commandes slash ont été désynchronisées globalement.",
                color=0xBEBEFE,
            )
            await context.send(embed=embed)
            return
        elif scope == "guild":
            context.bot.tree.clear_commands(guild=context.guild)
            await context.bot.tree.sync(guild=context.guild)
            embed = discord.Embed(
                description="Les commandes slash ont été désynchronisées dans ce serveur.",
                color=0xBEBEFE,
            )
            await context.send(embed=embed)
            return
        embed = discord.Embed(
            description="Le champ doit être `global` ou `guild`.", color=0xE02B2B
        )
        await context.send(embed=embed)

    @commands.hybrid_command(
        name="load",
        description="Charge un cog.",
    )
    @app_commands.describe(cog="Le nom du cog à charger")
    @commands.is_owner()
    async def load(self, context: Context, cog: str) -> None:
        """
        Le bot va charger le cog donné.

        :param context: Le contexte de la commande hybride.
        :param cog: Le nom du cog à charger.
        """
        try:
            await self.bot.load_extension(f"cogs.{cog}")
        except Exception:
            embed = discord.Embed(
                description=f"Impossible de charger le cog `{cog}`.", color=0xE02B2B
            )
            await context.send(embed=embed)
            return
        embed = discord.Embed(
            description=f"Le cog `{cog}` a été chargé avec succès.", color=0xBEBEFE
        )
        await context.send(embed=embed)

    @commands.hybrid_command(
        name="unload",
        description="Décharge un cog.",
    )
    @app_commands.describe(cog="Le nom du cog à décharger")
    @commands.is_owner()
    async def unload(self, context: Context, cog: str) -> None:
        """
        Le bot va décharger le cog donné.

        :param context: Le contexte de la commande hybride.
        :param cog: Le nom du cog à décharger.
        """
        try:
            await self.bot.unload_extension(f"cogs.{cog}")
        except Exception:
            embed = discord.Embed(
                description=f"Impossible de décharger le cog `{cog}`.", color=0xE02B2B
            )
            await context.send(embed=embed)
            return
        embed = discord.Embed(
            description=f"Le cog `{cog}` a été déchargé avec succès.", color=0xBEBEFE
        )
        await context.send(embed=embed)

    @commands.hybrid_command(
        name="reload",
        description="Recharge un cog.",
    )
    @app_commands.describe(cog="Le nom du cog à recharger")
    @commands.is_owner()
    async def reload(self, context: Context, cog: str) -> None:
        """
        Le bot va recharger le cog donné.

        :param context: Le contexte de la commande hybride.
        :param cog: Le nom du cog à recharger.
        """
        try:
            await self.bot.reload_extension(f"cogs.{cog}")
        except Exception:
            embed = discord.Embed(
                description=f"Impossible de recharger le cog `{cog}`.", color=0xE02B2B
            )
            await context.send(embed=embed)
            return
        embed = discord.Embed(
            description=f"Le cog `{cog}` a été rechargé avec succès.", color=0xBEBEFE
        )
        await context.send(embed=embed)

    @commands.hybrid_command(
        name="shutdown",
        description="Éteint le bot.",
    )
    @commands.is_owner()
    async def shutdown(self, context: Context) -> None:
        """
        Éteint le bot.

        :param context: Le contexte de la commande hybride.
        """
        embed = discord.Embed(description="Arrêt en cours. Au revoir ! :wave:", color=0xBEBEFE)
        await context.send(embed=embed)
        await self.bot.close()

    @commands.hybrid_command(
        name="say",
        description="Le bot dira tout ce que vous voulez.",
    )
    @app_commands.describe(message="Le message que le bot devrait répéter")
    @commands.is_owner()
    async def say(self, context: Context, *, message: str) -> None:
        """
        Le bot dira tout ce que vous voulez.

        :param context: Le contexte de la commande hybride.
        :param message: Le message que le bot devrait répéter.
        """
        await context.send(message)
        await context.message.delete()

    @commands.hybrid_command(
        name="embed",
        description="Le bot dira tout ce que vous voulez, mais dans un embed.",
    )
    @app_commands.describe(
        message="Le message que le bot devrait répéter",
        attachment="Les pièces jointes que le bot devrait envoyer"
    )
    @commands.is_owner()
    async def embed(self, context: Context, *, message: str, attachment: Optional[discord.Attachment] = None) -> None:
        """
        Le bot dira tout ce que vous voulez, mais en utilisant un embed.

        :param context: Le contexte de la commande hybride.
        :param message: Le message que le bot devrait répéter.
        :param attachment: Les pièces jointes que le bot devrait envoyer.
        """
        embed = discord.Embed(description=message, color=0xBEBEFE)
        if attachment:
            if attachment.size > 8 * 1024 * 1024:  # 8 MB
                embed = discord.Embed(
                    description="La taille de la pièce jointe doit être inférieure à 8 MB.", color=0xE02B2B
                )
                await context.send(embed=embed)
                return
            file = await attachment.to_file()
            await context.send(embed=embed, file=file)
        else:
            await context.send(embed=embed)
        await context.message.delete()


async def setup(bot) -> None:
    await bot.add_cog(Owner(bot))