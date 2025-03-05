import discord
from discord.ext import commands
from discord import app_commands
import json
import os
import math

class XP(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.xp_data = self.load_xp_data()
        self.messages_per_level = 400  # Nombre de messages requis pour niveau up
        # Dictionnaire pour stocker les canaux de level up par serveur
        self.level_up_channels = {
            "797781758841847808": 1104041737850196019,
            "1289627804211609640": 1336777782952198274,
        }

    def load_xp_data(self):
        if os.path.exists("xp_data.json"):
            try:
                with open("xp_data.json", "r") as f:
                    data = json.load(f)
                print("Données XP chargées avec succès.")
                return data
            except Exception as e:
                print(f"Erreur lors du chargement des données XP : {e}")
                return {}
        return {}

    def save_xp_data(self):
        try:
            with open("xp_data.json", "w") as f:
                json.dump(self.xp_data, f, indent=4)
        except Exception as e:
            print(f"Erreur lors de la sauvegarde des données XP : {e}")

    def calculate_level(self, messages):
        """Calcule le niveau basé sur le nombre de messages (1 niveau tous les 400 messages)"""
        return (messages // self.messages_per_level) + 1

    def calculate_messages_for_next_level(self, messages):
        """Calcule le nombre de messages restants pour le prochain niveau"""
        current_level = self.calculate_level(messages)
        messages_needed = (current_level * self.messages_per_level)
        return messages_needed - messages

    async def add_message(self, user_id, guild_id):
        """Ajoute un message au compteur de l'utilisateur"""
        server_id = str(guild_id)
        user_id = str(user_id)

        # Initialise la structure de données si elle n'existe pas
        if server_id not in self.xp_data:
            self.xp_data[server_id] = {}

        # Structure de données par défaut pour un nouvel utilisateur
        default_data = {
            "messages": 0,
            "level": 1
        }

        # Initialise ou récupère les données de l'utilisateur
        if user_id not in self.xp_data[server_id]:
            self.xp_data[server_id][user_id] = default_data.copy()

        # Incrémente le compteur de messages
        self.xp_data[server_id][user_id]["messages"] += 1
        messages = self.xp_data[server_id][user_id]["messages"]
        current_level = self.xp_data[server_id][user_id]["level"]
        new_level = self.calculate_level(messages)

        # Vérifie si l'utilisateur a gagné un niveau
        if new_level > current_level:
            self.xp_data[server_id][user_id]["level"] = new_level
            await self.notify_level_up(user_id, server_id, new_level)

        self.save_xp_data()

    async def notify_level_up(self, user_id, server_id, new_level):
        try:
            channel_id = self.level_up_channels.get(server_id)
            if not channel_id:
                return

            channel = self.bot.get_channel(channel_id)
            if not channel:
                return

            user = await self.bot.fetch_user(int(user_id))
            if not user:
                return

            embed = discord.Embed(
                title="🎉 Level Up!",
                description=f"{user.mention} has reached level {new_level}!",
                color=discord.Color.gold()
            )
            embed.set_thumbnail(url=user.display_avatar.url)
            await channel.send(embed=embed)

        except Exception as e:
            print(f"[XP] Erreur notification: {e}")

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot or not message.guild:
            return
        await self.add_message(message.author.id, message.guild.id)

    @app_commands.command(
        name="rank",
        description="Display your rank or another user's rank and progress"
    )
    @app_commands.describe(
        user="The user to check (leave empty to see your own rank)"
    )
    async def rank(self, interaction: discord.Interaction, user: discord.Member = None):
        server_id = str(interaction.guild_id)
        target_user = user or interaction.user
        user_id = str(target_user.id)

        # Initialize default data
        default_data = {
            "messages": 0,
            "level": 1
        }

        # Get user data or use default
        if server_id not in self.xp_data:
            self.xp_data[server_id] = {}
        
        data = self.xp_data[server_id].get(user_id, default_data)
        messages = data["messages"]
        level = self.calculate_level(messages)
        next_level_messages = self.calculate_messages_for_next_level(messages)

        embed = discord.Embed(
            title=f"📊 Statistics for {target_user.display_name}",
            color=target_user.color
        )
        embed.set_thumbnail(url=target_user.display_avatar.url)
        
        # Trouve le rang de l'utilisateur
        all_users = [(uid, udata) for uid, udata in self.xp_data[server_id].items()]
        sorted_users = sorted(all_users, key=lambda x: (x[1].get("level", 1), x[1].get("messages", 0)), reverse=True)
        rank = next((index + 1 for index, (uid, _) in enumerate(sorted_users) if uid == user_id), 0)
        
        embed.add_field(name="Rank", value=f"```#{rank}```", inline=True)
        embed.add_field(name="Level", value=f"```{level}```", inline=True)
        embed.add_field(name="Messages", value=f"```{messages}```", inline=True)
        
        # Barre de progression
        progress = (messages % self.messages_per_level) / self.messages_per_level
        bar_length = 10
        filled = int(progress * bar_length)
        bar = "█" * filled + "░" * (bar_length - filled)
        
        embed.add_field(
            name="Progression",
            value=f"{bar} {int(progress * 100)}%\n{next_level_messages} messages left for level {level + 1}",
            inline=False
        )

        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="leaderboard", description="Displays server ranking")
    async def leaderboard(self, interaction: discord.Interaction):
        server_id = str(interaction.guild_id)
        
        if server_id not in self.xp_data:
            await interaction.response.send_message("Aucune donnée pour ce serveur!", ephemeral=True)
            return

        # Filtre les utilisateurs avec des données valides
        valid_users = []
        for user_id, data in self.xp_data[server_id].items():
            if isinstance(data, dict) and "messages" in data and "level" in data:
                valid_users.append((user_id, data))

        # Trie les utilisateurs valides
        sorted_users = sorted(
            valid_users,
            key=lambda x: (x[1].get("level", 1), x[1].get("messages", 0)),
            reverse=True
        )[:10]

        embed = discord.Embed(
            title=f"🏆 Ranking of - {interaction.guild.name}",
            color=discord.Color.gold()
        )

        if not sorted_users:
            embed.description = "No valid data to display"
        else:
            for rank, (user_id, data) in enumerate(sorted_users, 1):
                user = interaction.guild.get_member(int(user_id))
                if user:
                    medal = {1: "🥇", 2: "🥈", 3: "🥉"}.get(rank, "")
                    embed.add_field(
                        name=f"{medal} #{rank} {user.display_name}",
                        value=f"Level {data.get('level', 1)} | {data.get('messages', 0)} messages",
                        inline=False
                    )

        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="resetxp", description="Resets a member's XP")
    @app_commands.checks.has_permissions(administrator=True)
    async def resetxp(self, interaction: discord.Interaction, member: discord.Member):
        server_id = str(interaction.guild_id)
        user_id = str(member.id)

        if server_id in self.xp_data and user_id in self.xp_data[server_id]:
            self.xp_data[server_id][user_id] = {"messages": 0, "level": 1}
            self.save_xp_data()
            await interaction.response.send_message(
                f"“The statistics of {member.name} have been reset.",
                ephemeral=True
            )
        else:
            await interaction.response.send_message(
                f"{member.name} has no statistics to reset.",
                ephemeral=True
            )

    @app_commands.command(name="setlevelup", description="Configures the level notification lounge")
    @app_commands.checks.has_permissions(administrator=True)
    async def setlevelup(self, interaction: discord.Interaction, channel: discord.TextChannel = None):
        channel = channel or interaction.channel
        server_id = str(interaction.guild_id)
        
        self.level_up_channels[server_id] = channel.id
        await interaction.response.send_message(
            f"Salon de niveau configuré sur {channel.mention}",
            ephemeral=True
        )

async def setup(bot):
    await bot.add_cog(XP(bot))