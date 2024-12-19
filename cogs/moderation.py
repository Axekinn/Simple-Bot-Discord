"""
Copyright © Krypton 2019-Present - https://github.com/kkrypt0nn (https://krypton.ninja)
Description:
🐍 A simple template to start to code your own and personalized Discord bot in Python

Version: 6.2.0
"""

import os
from datetime import datetime

import discord
from discord import app_commands
from discord.ext import commands
from discord.ext.commands import Context


class Moderation(commands.Cog, name="modération"):
    def __init__(self, bot) -> None:
        self.bot = bot

    @commands.hybrid_command(
        name="kick",
        description="Expulse un utilisateur du serveur.",
    )
    @commands.has_permissions(kick_members=True)
    @commands.bot_has_permissions(kick_members=True)
    @app_commands.describe(
        user="L'utilisateur qui doit être expulsé.",
        reason="La raison pour laquelle l'utilisateur doit être expulsé.",
    )
    async def kick(
        self, context: Context, user: discord.User, *, reason: str = "Non spécifiée"
    ) -> None:
        """
        Expulse un utilisateur du serveur.

        :param context: Le contexte de la commande hybride.
        :param user: L'utilisateur qui doit être expulsé du serveur.
        :param reason: La raison de l'expulsion. Par défaut : "Non spécifiée".
        """
        member = context.guild.get_member(user.id) or await context.guild.fetch_member(
            user.id
        )
        if member.guild_permissions.administrator:
            embed = discord.Embed(
                description="L'utilisateur a des permissions d'administrateur.",
                color=0xE02B2B
            )
            await context.send(embed=embed)
        else:
            try:
                embed = discord.Embed(
                    description=f"**{member}** a été expulsé par **{context.author}** !",
                    color=0xBEBEFE,
                )
                embed.add_field(name="Raison :", value=reason)
                await context.send(embed=embed)
                try:
                    await member.send(
                        f"Vous avez été expulsé de **{context.guild.name}** par **{context.author}**.\nRaison : {reason}"
                    )
                except:
                    pass
                await member.kick(reason=reason)
            except:
                pass

    @commands.hybrid_command(
        name="nick",
        description="Change le surnom d'un utilisateur sur le serveur.",
    )
    @commands.has_permissions(manage_nicknames=True)
    @commands.bot_has_permissions(manage_nicknames=True)
    @app_commands.describe(
        user="L'utilisateur qui devrait avoir un nouveau surnom.",
        nickname="Le nouveau surnom qui doit être défini.",
    )
    async def nick(
        self, context: Context, user: discord.User, *, nickname: str = None
    ) -> None:
        """
        Change le surnom d'un utilisateur sur le serveur.

        :param context: Le contexte de la commande hybride.
        :param user: L'utilisateur dont le surnom doit être changé.
        :param nickname: Le nouveau surnom de l'utilisateur. Par défaut, None, ce qui réinitialisera le surnom.
        """
        member = context.guild.get_member(user.id) or await context.guild.fetch_member(
            user.id
        )
        try:
            await member.edit(nick=nickname)
            embed = discord.Embed(
                description=f"Le nouveau surnom de **{member}** est **{nickname}** !",
                color=0xBEBEFE,
            )
            await context.send(embed=embed)
        except:
            embed = discord.Embed(
                description="Une erreur s'est produite lors de la tentative de changement du surnom de l'utilisateur. Assurez-vous que mon rôle est au-dessus du rôle de l'utilisateur dont vous voulez changer le surnom.",
                color=0xE02B2B,
            )
            await context.send(embed=embed)

    @commands.hybrid_command(
        name="ban",
        description="Bannit un utilisateur du serveur.",
    )
    @commands.has_permissions(ban_members=True)
    @commands.bot_has_permissions(ban_members=True)
    @app_commands.describe(
        user="L'utilisateur qui doit être banni.",
        reason="La raison pour laquelle l'utilisateur doit être banni.",
    )
    async def ban(
        self, ctx: commands.Context, user: discord.User, *, reason: str = "Non spécifiée"
    ) -> None:
        """
        Bannit un utilisateur du serveur.

        :param ctx: Le contexte de la commande hybride.
        :param user: L'utilisateur qui doit être banni du serveur.
        :param reason: La raison du bannissement. Par défaut : "Non spécifiée".
        """
        member = ctx.guild.get_member(user.id) or await ctx.guild.fetch_member(user.id)

        if member.guild_permissions.administrator:
            embed = discord.Embed(
                description="⚠️ Vous ne pouvez pas bannir un administrateur.",
                color=0xE02B2B,
            )
            await ctx.send(embed=embed)
            return

        try:
            await member.ban(reason=reason)
            embed = discord.Embed(
                description=f"✅ **{member}** a été banni par **{ctx.author}** !",
                color=0xBEBEFE,
            )
            embed.add_field(name="Raison :", value=reason)
            await ctx.send(embed=embed)
            try:
                await member.send(
                    f"Vous avez été banni de **{ctx.guild.name}** par **{ctx.author}**.\nRaison : {reason}"
                )
            except discord.Forbidden:
                # L'utilisateur a peut-être désactivé les messages privés
                pass
        except discord.Forbidden:
            embed = discord.Embed(
                title="Erreur",
                description="Je n'ai pas les permissions nécessaires pour bannir cet utilisateur.",
                color=0xE02B2B,
            )
            await ctx.send(embed=embed)
        except Exception as e:
            embed = discord.Embed(
                title="Erreur",
                description=f"Une erreur est survenue : {e}",
                color=0xE02B2B,
            )
            await ctx.send(embed=embed)

    @commands.hybrid_group(
        name="warning",
        description="Gère les avertissements d'un utilisateur sur le serveur.",
    )
    @commands.has_permissions(manage_messages=True)
    async def warning(self, context: Context) -> None:
        """
        Gère les avertissements d'un utilisateur sur le serveur.

        :param context: Le contexte de la commande hybride.
        """
        if context.invoked_subcommand is None:
            embed = discord.Embed(
                description="Veuillez spécifier une sous-commande.\n\n**Sous-commandes :**\n`add` - Ajoute un avertissement à un utilisateur.\n`remove` - Supprime un avertissement d'un utilisateur.\n`list` - Liste tous les avertissements d'un utilisateur.",
                color=0xE02B2B,
            )
            await context.send(embed=embed)

    @warning.command(
        name="add",
        description="Ajoute un avertissement à un utilisateur dans le serveur.",
    )
    @commands.has_permissions(manage_messages=True)
    @app_commands.describe(
        user="L'utilisateur qui doit être averti.",
        reason="La raison pour laquelle l'utilisateur doit être averti.",
    )
    async def warning_add(
        self, context: Context, user: discord.User, *, reason: str = "Non spécifiée"
    ) -> None:
        """
        Avertit un utilisateur dans ses messages privés.

        :param context: Le contexte de la commande hybride.
        :param user: L'utilisateur qui doit être averti.
        :param reason: La raison de l'avertissement. Par défaut : "Non spécifiée".
        """
        member = context.guild.get_member(user.id) or await context.guild.fetch_member(
            user.id
        )
        total = await self.bot.database.add_warn(
            user.id, context.guild.id, context.author.id, reason
        )
        embed = discord.Embed(
            description=f"**{member}** a été averti par **{context.author}** !\nTotal des avertissements pour cet utilisateur : {total}",
            color=0xBEBEFE,
        )
        embed.add_field(name="Raison :", value=reason)
        await context.send(embed=embed)
        try:
            await member.send(
                f"Vous avez été averti par **{context.author}** dans **{context.guild.name}** !\nRaison : {reason}"
            )
        except:
            await context.send(
                f"{member.mention}, vous avez été averti par **{context.author}** !\nRaison : {reason}"
            )

    @warning.command(
        name="remove",
        description="Supprime un avertissement d'un utilisateur dans le serveur.",
    )
    @commands.has_permissions(manage_messages=True)
    @app_commands.describe(
        user="L'utilisateur dont l'avertissement doit être supprimé.",
        warn_id="L'ID de l'avertissement qui doit être supprimé.",
    )
    async def warning_remove(
        self, context: Context, user: discord.User, warn_id: int
    ) -> None:
        """
        Supprime un avertissement d'un utilisateur.

        :param context: Le contexte de la commande hybride.
        :param user: L'utilisateur dont l'avertissement doit être supprimé.
        :param warn_id: L'ID de l'avertissement qui doit être supprimé.
        """
        member = context.guild.get_member(user.id) or await context.guild.fetch_member(
            user.id
        )
        total = await self.bot.database.remove_warn(warn_id, user.id, context.guild.id)
        embed = discord.Embed(
            description=f"J'ai supprimé l'avertissement **#{warn_id}** de **{member}** !\nTotal des avertissements pour cet utilisateur : {total}",
            color=0xBEBEFE,
        )
        await context.send(embed=embed)

    @warning.command(
        name="list",
        description="Affiche les avertissements d'un utilisateur dans le serveur.",
    )
    @commands.has_guild_permissions(manage_messages=True)
    @app_commands.describe(user="L'utilisateur dont vous voulez voir les avertissements.")
    async def warning_list(self, context: Context, user: discord.User) -> None:
        """
        Affiche les avertissements d'un utilisateur dans le serveur.

        :param context: Le contexte de la commande hybride.
        :param user: L'utilisateur dont vous voulez voir les avertissements.
        """
        warnings_list = await self.bot.database.get_warnings(user.id, context.guild.id)
        embed = discord.Embed(title=f"Avertissements de {user}", color=0xBEBEFE)
        description = ""
        if len(warnings_list) == 0:
            description = "Cet utilisateur n'a aucun avertissement."
        else:
            for warning in warnings_list:
                pass
        embed.description = description
        await context.send(embed=embed)

    @commands.hybrid_command(
        name="purge",
        description="Supprime un nombre de messages.",
    )
    @commands.has_guild_permissions(manage_messages=True)
    @commands.bot_has_permissions(manage_messages=True)
    @app_commands.describe(amount="Le nombre de messages à supprimer.")
    async def purge(self, context: Context, amount: int) -> None:
        """
        Supprime un nombre de messages.

        :param context: Le contexte de la commande hybride.
        :param amount: Le nombre de messages à supprimer.
        """
        await context.send(
            "Suppression des messages..."
        )
        purged_messages = await context.channel.purge(limit=amount + 1)
        embed = discord.Embed(
            description=f"**{context.author}** a supprimé **{len(purged_messages)-1}** messages !",
            color=0xBEBEFE,
        )
        await context.channel.send(embed=embed)

    @commands.hybrid_command(
        name="hackban",
        description="Bannit un utilisateur sans qu'il soit dans le serveur.",
    )
    @commands.has_permissions(ban_members=True)
    @commands.bot_has_permissions(ban_members=True)
    @app_commands.describe(
        user_id="L'ID de l'utilisateur qui doit être banni.",
        reason="La raison pour laquelle l'utilisateur doit être banni.",
    )
    async def hackban(
        self, context: Context, user_id: str, *, reason: str = "Non spécifiée"
    ) -> None:
        """
        Bannit un utilisateur sans qu'il soit dans le serveur.

        :param context: Le contexte de la commande hybride.
        :param user_id: L'ID de l'utilisateur qui doit être banni.
        :param reason: La raison du bannissement. Par défaut : "Non spécifiée".
        """
        try:
            await self.bot.http.ban(user_id, context.guild.id, reason=reason)
            user = self.bot.get_user(int(user_id)) or await self.bot.fetch_user(
                int(user_id)
            )
            embed = discord.Embed(
                description=f"**{user}** (ID : {user_id}) a été banni par **{context.author}** !",
                color=0xBEBEFE,
            )
            embed.add_field(name="Raison :", value=reason)
            await context.send(embed=embed)
        except Exception:
            embed = discord.Embed(
                description="Une erreur s'est produite lors de la tentative de bannissement de l'utilisateur. Assurez-vous que l'ID est un ID existant appartenant à un utilisateur.",
                color=0xE02B2B,
            )
            await context.send(embed=embed)

    @commands.hybrid_command(
        name="archive",
        description="Archive les derniers messages dans un fichier texte avec une limite choisie.",
    )
    @commands.has_permissions(manage_messages=True)
    @app_commands.describe(
        limit="La limite de messages à archiver.",
    )
    async def archive(self, context: Context, limit: int = 10) -> None:
        """
        Archive les derniers messages dans un fichier texte avec une limite choisie. Cette commande nécessite l'intention MESSAGE_CONTENT pour fonctionner correctement.

        :param limit: La limite de messages à archiver. Par défaut : 10.
        """
        log_file = f"{context.channel.id}.log"
        with open(log_file, "w", encoding="UTF-8") as f:
            f.write(
                f'Messages archivés de : #{context.channel} ({context.channel.id}) dans le serveur "{context.guild}" ({context.guild.id}) le {datetime.now().strftime("%d.%m.%Y %H:%M:%S")}\n'
            )
            async for message in context.channel.history(
                limit=limit, before=context.message
            ):
                pass
        f = discord.File(log_file)
        await context.send(file=f)
        os.remove(log_file)


async def setup(bot) -> None:
    await bot.add_cog(Moderation(bot))