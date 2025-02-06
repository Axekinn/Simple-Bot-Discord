import discord
from discord.ext import commands
from discord import app_commands
from typing import Dict, List

class RoleReaction(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        # Format: {message_id: {emoji: role_id}}
        self.role_messages: Dict[int, Dict[str, int]] = {}

    @app_commands.command(
        name="setup_roles",
        description="Creates a message enabling several roles to be obtained via several reactions."
    )
    @app_commands.describe(
        roles="List of roles (mentions) separated by a comma, e.g: @Role1, @Role2",
        emojis="List of emojis separated by a comma, e.g.: ✅,❌"
    )
    async def setup_roles(
        self,
        interaction: discord.Interaction,
        roles: str,
        emojis: str
    ):
        # Vérifie la permission administrateur
        if not interaction.user.guild_permissions.administrator:
            return await interaction.response.send_message("🚫 You do not have permission", ephemeral=True)

        # Convertit les chaînes de rôles et d'emojis en listes
        role_mentions = [r.strip() for r in roles.split(',')]
        emoji_list = [e.strip() for e in emojis.split(',')]

        # Vérifie que le nombre de rôles et d'emojis correspond
        if len(role_mentions) != len(emoji_list):
            return await interaction.response.send_message(
                f"Please provide as many emojis as you have roles.\n"
                f"Rôles: {len(role_mentions)} | Emojis: {len(emoji_list)}",
                ephemeral=True
            )

        embed = discord.Embed(
            title="Assigning roles",
            description=""
        )

        # Essayez de récupérer les objets Role depuis les mentions
        guild = interaction.guild
        parsed_roles: List[discord.Role] = []
        for r_mention in role_mentions:
            # Récupère l'ID du rôle depuis la mention <@&...>
            role_id = r_mention.replace("<@&", "").replace(">", "").strip()
            role_obj = guild.get_role(int(role_id)) if role_id.isdigit() else None
            if role_obj:
                parsed_roles.append(role_obj)
            else:
                return await interaction.response.send_message(
                    f"Rôle `{r_mention}` is missing.",
                    ephemeral=True
                )

        # Construit le message d'explication
        for i, role_obj in enumerate(parsed_roles):
            embed.description += f"{emoji_list[i]} → {role_obj.mention}\n"

        # Envoie le message
        message = await interaction.channel.send(embed=embed)
        self.role_messages[message.id] = {}

        # Ajoute chaque couple (emoji -> role)
        for i, role_obj in enumerate(parsed_roles):
            try:
                await message.add_reaction(emoji_list[i])
                self.role_messages[message.id][emoji_list[i]] = role_obj.id
            except discord.HTTPException:
                # En cas d'emoji invalide
                pass

        await interaction.response.send_message("Done !", ephemeral=True)

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload: discord.RawReactionActionEvent):
        # Vérifie si le message est concerné
        if payload.message_id not in self.role_messages:
            return

        emoji_str = str(payload.emoji)
        if emoji_str in self.role_messages[payload.message_id]:
            guild = self.bot.get_guild(payload.guild_id)
            role = guild.get_role(self.role_messages[payload.message_id][emoji_str])
            member = await guild.fetch_member(payload.user_id)
            if member and member.id != self.bot.user.id:
                await member.add_roles(role)

    @commands.Cog.listener()
    async def on_raw_reaction_remove(self, payload: discord.RawReactionActionEvent):
        # Vérifie si le message est concerné
        if payload.message_id not in self.role_messages:
            return

        emoji_str = str(payload.emoji)
        if emoji_str in self.role_messages[payload.message_id]:
            guild = self.bot.get_guild(payload.guild_id)
            role = guild.get_role(self.role_messages[payload.message_id][emoji_str])
            member = await guild.fetch_member(payload.user_id)
            if member and member.id != self.bot.user.id:
                await member.remove_roles(role)

async def setup(bot):
    await bot.add_cog(RoleReaction(bot))