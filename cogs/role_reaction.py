import discord
from discord.ext import commands
from discord import app_commands
from typing import Dict, List

class RoleReaction(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        # Format: {message_id: {emoji_id_or_unicode: role_id}}
        self.role_messages: Dict[int, Dict[str, int]] = {}

    def parse_emoji(self, emoji_str: str) -> tuple[str, str]:
        """
        Parse un emoji personnalisé ou unicode
        Retourne (emoji_str, emoji_display)
        """
        # Si c'est un emoji personnalisé (<:name:id>)
        if emoji_str.startswith('<:') and emoji_str.endswith('>'):
            try:
                name, id = emoji_str.strip('<:>').rsplit(':', 1)
                return emoji_str, f"<:{name}:{id}>"
            except ValueError:
                return emoji_str, emoji_str
        # Si c'est un emoji animé (<a:name:id>)
        elif emoji_str.startswith('<a:') and emoji_str.endswith('>'):
            try:
                name, id = emoji_str.strip('<a:>').rsplit(':', 1)
                return emoji_str, f"<a:{name}:{id}>"
            except ValueError:
                return emoji_str, emoji_str
        return emoji_str, emoji_str

    @app_commands.command(
        name="setup_roles",
        description="Creates a message enabling several roles to be obtained via several reactions."
    )
    @app_commands.describe(
        roles="List of roles (mentions) separated by a comma, e.g: @Role1, @Role2",
        emojis="List of emojis (custom or unicode) separated by a comma, e.g.: ✅,❌,<:custom:123456789>"
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
        parsed_emojis = [self.parse_emoji(e) for e in emoji_list]

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
            emoji_str, emoji_display = parsed_emojis[i]
            embed.description += f"{emoji_display} → {role_obj.mention}\n"

        # Envoie le message
        message = await interaction.channel.send(embed=embed)
        self.role_messages[message.id] = {}

        # Ajoute chaque couple (emoji -> role)
        for i, role_obj in enumerate(parsed_roles):
            try:
                emoji_str, emoji_display = parsed_emojis[i]
                if emoji_str.startswith('<') and ':' in emoji_str:
                    # Pour les émojis personnalisés
                    try:
                        # Extraction de l'ID de l'emoji
                        if emoji_str.startswith('<a:'): # Emoji animé
                            name, emoji_id = emoji_str.strip('<a:>').rsplit(':', 1)
                            emoji_id = int(emoji_id.rstrip('>'))
                            # Cherche l'emoji dans le serveur
                            emoji = discord.utils.get(interaction.guild.emojis, id=emoji_id)
                            if not emoji:
                                print(f"Emoji {name} ({emoji_id}) non trouvé sur le serveur")
                                continue
                        else: # Emoji normal
                            name, emoji_id = emoji_str.strip('<:>').rsplit(':', 1)
                            emoji_id = int(emoji_id.rstrip('>'))
                            # Cherche l'emoji dans le serveur
                            emoji = discord.utils.get(interaction.guild.emojis, id=emoji_id)
                            if not emoji:
                                print(f"Emoji {name} ({emoji_id}) non trouvé sur le serveur")
                                continue
                        
                        await message.add_reaction(emoji)
                    except (ValueError, discord.HTTPException) as e:
                        print(f"Erreur lors de l'ajout de la réaction {emoji_str}: {e}")
                        continue
                else:
                    # Pour les émojis Unicode
                    await message.add_reaction(emoji_str)
                
                # Stocke l'emoji sous sa forme complète pour la comparaison plus tard
                if isinstance(emoji, discord.Emoji):
                    stored_emoji = str(emoji)
                else:
                    stored_emoji = emoji_str
                self.role_messages[message.id][stored_emoji] = role_obj.id
                
            except Exception as e:
                print(f"Erreur lors de l'ajout de la réaction {emoji_str}: {e}")
                continue

        await interaction.response.send_message("Done!", ephemeral=True)

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload: discord.RawReactionActionEvent):
        if payload.message_id not in self.role_messages:
            return

        # Gestion des émojis personnalisés et Unicode
        if payload.emoji.id:
            emoji_str = f"<:{payload.emoji.name}:{payload.emoji.id}>"
        else:
            emoji_str = str(payload.emoji)

        if emoji_str in self.role_messages[payload.message_id]:
            guild = self.bot.get_guild(payload.guild_id)
            role = guild.get_role(self.role_messages[payload.message_id][emoji_str])
            member = await guild.fetch_member(payload.user_id)
            if member and member.id != self.bot.user.id:
                await member.add_roles(role)

    @commands.Cog.listener()
    async def on_raw_reaction_remove(self, payload: discord.RawReactionActionEvent):
        if payload.message_id not in self.role_messages:
            return

        # Gestion des émojis personnalisés et Unicode
        if payload.emoji.id:
            emoji_str = f"<:{payload.emoji.name}:{payload.emoji.id}>"
        else:
            emoji_str = str(payload.emoji)

        if emoji_str in self.role_messages[payload.message_id]:
            guild = self.bot.get_guild(payload.guild_id)
            role = guild.get_role(self.role_messages[payload.message_id][emoji_str])
            member = await guild.fetch_member(payload.user_id)
            if member and member.id != self.bot.user.id:
                await member.remove_roles(role)

async def setup(bot):
    await bot.add_cog(RoleReaction(bot))