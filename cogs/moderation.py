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


class Moderation(commands.Cog, name="moderation"):
    def __init__(self, bot) -> None:
        self.bot = bot

    @commands.hybrid_command(
        name="kick",
        description="Expels a user from the server.",
    )
    @commands.has_permissions(kick_members=True)
    @commands.bot_has_permissions(kick_members=True)
    @app_commands.describe(
        user="The user to be expelled.",
        reason="The reason why the user must be evicted.",
    )
    async def kick(
        self, context: Context, user: discord.User, *, reason: str = "Not specified"
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
                description="The user has administrator permissions.",
                color=0xE02B2B
            )
            await context.send(embed=embed)
        else:
            try:
                embed = discord.Embed(
                    description=f"**{member}** was expelled by **{context.author}** !",
                    color=0xBEBEFE,
                )
                embed.add_field(name="Reason :", value=reason)
                await context.send(embed=embed)
                try:
                    await member.send(
                        f"You have been expelled from **{context.guild.name}** by **{context.author}**.\nReason : {reason}"
                    )
                except:
                    pass
                await member.kick(reason=reason)
            except:
                pass

    @commands.hybrid_command(
        name="nick",
        description="Changes a user's nickname on the server.",
    )
    @commands.has_permissions(manage_nicknames=True)
    @commands.bot_has_permissions(manage_nicknames=True)
    @app_commands.describe(
        user="The user who should have a new nickname.",
        nickname="The new nickname to be defined.",
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
                description=f"The new nickname for **{member}** is **{nickname}** !",
                color=0xBEBEFE,
            )
            await context.send(embed=embed)
        except:
            embed = discord.Embed(
                description="An error occurred when attempting to change the user's nickname. Make sure my role is above the role of the user whose nickname you want to change.",
                color=0xE02B2B,
            )
            await context.send(embed=embed)

    @commands.hybrid_command(
        name="ban",
        description="Bans a user from the server.",
    )
    @commands.has_permissions(ban_members=True)
    @commands.bot_has_permissions(ban_members=True)
    @app_commands.describe(
        user="The user to be banned.",
        reason="The reason why the user should be banned.",
    )
    async def ban(
        self, ctx: commands.Context, user: discord.User, *, reason: str = "Not specified"
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
                description="⚠️ You cannot ban an administrator.",
                color=0xE02B2B,
            )
            await ctx.send(embed=embed)
            return

        try:
            await member.ban(reason=reason)
            embed = discord.Embed(
                description=f"✅ **{member}** has been banned by **{ctx.author}** !",
                color=0xBEBEFE,
            )
            embed.add_field(name="Reason :", value=reason)
            await ctx.send(embed=embed)
            try:
                await member.send(
                    f"You have been banned from **{ctx.guild.name}** by **{ctx.author}**.\nReason : {reason}"
                )
            except discord.Forbidden:
                # L'utilisateur a peut-être désactivé les messages privés
                pass
        except discord.Forbidden:
            embed = discord.Embed(
                title="Error",
                description="I don't have the necessary permissions to ban this user.",
                color=0xE02B2B,
            )
            await ctx.send(embed=embed)
        except Exception as e:
            embed = discord.Embed(
                title="Error",
                description=f"An error has occurred : {e}",
                color=0xE02B2B,
            )
            await ctx.send(embed=embed)

    @commands.hybrid_group(
        name="warning",
        description="Manages user warnings on the server.",
    )
    @commands.has_permissions(manage_messages=True)
    async def warning(self, context: Context) -> None:
        """
        Gère les avertissements d'un utilisateur sur le serveur.

        :param context: Le contexte de la commande hybride.
        """
        if context.invoked_subcommand is None:
            embed = discord.Embed(
                description="Please specify a sub-order.\n\n**Sub-orders :**\n`add` - Adds a warning to a user.\n`remove` - Removes a user warning.\n`list` - Lists all warnings for a user.",
                color=0xE02B2B,
            )
            await context.send(embed=embed)

    @warning.command(
        name="add",
        description="Adds a warning to a user in the server.",
    )
    @commands.has_permissions(manage_messages=True)
    @app_commands.describe(
        user="The user who needs to be warned.",
        reason="The reason why the user must be warned.",
    )
    async def warning_add(
        self, context: Context, user: discord.User, *, reason: str = "Not specified"
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
            description=f"**{member}** has been notified by **{context.author}** !\nTotal warnings for this user : {total}",
            color=0xBEBEFE,
        )
        embed.add_field(name="Reason :", value=reason)
        await context.send(embed=embed)
        try:
            await member.send(
                f"You have been notified by **{context.author}** in **{context.guild.name}** !\nReason : {reason}"
            )
        except:
            await context.send(
                f"{member.mention}, you have been notified by **{context.author}** !\nReason : {reason}"
            )

    @warning.command(
        name="remove",
        description="Removes a user's warning from the server.",
    )
    @commands.has_permissions(manage_messages=True)
    @app_commands.describe(
        user="The user whose warning is to be removed.",
        warn_id="The ID of the warning to be deleted.",
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
            description=f"I've removed the warning **#{warn_id}** of **{member}** !\nTotal warnings for this user : {total}",
            color=0xBEBEFE,
        )
        await context.send(embed=embed)

    @warning.command(
        name="list",
        description="Displays a user's warnings in the server.",
    )
    @commands.has_guild_permissions(manage_messages=True)
    @app_commands.describe(user="The user whose warnings you want to see.")
    async def warning_list(self, context: Context, user: discord.User) -> None:
        """
        Affiche les avertissements d'un utilisateur dans le serveur.

        :param context: Le contexte de la commande hybride.
        :param user: L'utilisateur dont vous voulez voir les avertissements.
        """
        warnings_list = await self.bot.database.get_warnings(user.id, context.guild.id)
        embed = discord.Embed(title=f"Warnings from {user}", color=0xBEBEFE)
        description = ""
        if len(warnings_list) == 0:
            description = "This user has no warnings."
        else:
            for warning in warnings_list:
                pass
        embed.description = description
        await context.send(embed=embed)

    @commands.hybrid_command(
        name="purge",
        description="Deletes a number of messages.",
    )
    @commands.has_guild_permissions(manage_messages=True)
    @commands.bot_has_permissions(manage_messages=True)
    @app_commands.describe(amount="The number of messages to delete.")
    async def purge(self, context: Context, amount: int) -> None:
        """
        Supprime un nombre de messages.

        :param context: Le contexte de la commande hybride.
        :param amount: Le nombre de messages à supprimer.
        """
        await context.send(
            "Deleting messages..."
        )
        purged_messages = await context.channel.purge(limit=amount + 1)
        embed = discord.Embed(
            description=f"**{context.author}** has deleted **{len(purged_messages)-1}** messages !",
            color=0xBEBEFE,
        )
        await context.channel.send(embed=embed)

    @commands.hybrid_command(
        name="hackban",
        description="Bans a user from the server.",
    )
    @commands.has_permissions(ban_members=True)
    @commands.bot_has_permissions(ban_members=True)
    @app_commands.describe(
        user_id="The ID of the user to be banned.",
        reason="The reason why the user should be banned.",
    )
    async def hackban(
        self, context: Context, user_id: str, *, reason: str = "Not specified"
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
                description=f"**{user}** (ID : {user_id}) has been banned by **{context.author}** !",
                color=0xBEBEFE,
            )
            embed.add_field(name="Reason :", value=reason)
            await context.send(embed=embed)
        except Exception:
            embed = discord.Embed(
                description="An error occurred when attempting to ban the user. Make sure the ID is an existing user ID.",
                color=0xE02B2B,
            )
            await context.send(embed=embed)

    @commands.hybrid_command(
        name="archive",
        description="Archive the latest messages in a text file with a chosen limit.",
    )
    @commands.has_permissions(manage_messages=True)
    @app_commands.describe(
        limit="The limit of messages to be archived.",
    )
    async def archive(self, context: Context, limit: int = 10) -> None:
        """
        Archive les derniers messages dans un fichier texte avec une limite choisie. Cette commande nécessite l'intention MESSAGE_CONTENT pour fonctionner correctement.

        :param limit: La limite de messages à archiver. Par défaut : 10.
        """
        log_file = f"{context.channel.id}.log"
        with open(log_file, "w", encoding="UTF-8") as f:
            f.write(
                f'Archived messages from : #{context.channel} ({context.channel.id}) in the server "{context.guild}" ({context.guild.id}) le {datetime.now().strftime("%d.%m.%Y %H:%M:%S")}\n'
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