import discord
from discord.ext import commands
from discord.ext.commands import Context
import json
import os
import math

class XP(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.xp_data = self.load_xp_data()
        # Dictionnaire pour stocker les canaux de level up par serveur
        self.level_up_channels = {
            "797781758841847808": 1104041737850196019,  # Serveur 1
            "1289627804211609640": 1336777782952198274,  # Serveur 2
        }

    def load_xp_data(self):
        if os.path.exists("xp_data.json"):
            try:
                with open("xp_data.json", "r") as f:
                    data = json.load(f)
                print("Données XP chargées avec succès.")
                return data
            except json.JSONDecodeError:
                print("Erreur : xp_data.json n'est pas un JSON valide. Initialisation des données XP vides.")
                return {}
            except Exception as e:
                print(f"Erreur inattendue lors du chargement des données XP : {e}")
                return {}
        else:
            print("xp_data.json non trouvé. Initialisation des données XP vides.")
            return {}

    def save_xp_data(self):  # Suppression du async
        try:
            with open("xp_data.json", "w") as f:
                json.dump(self.xp_data, f, indent=4)
            print("Données XP sauvegardées avec succès")
        except Exception as e:
            print(f"Erreur lors de la sauvegarde des données XP : {e}")

    def calculate_level(self, xp):
        return math.floor(xp / 300) + 1

    async def add_xp(self, user_id, guild_id, xp_amount):
        server_id = str(guild_id)
        user_id = str(user_id)
        
        try:
            # Initialise la structure du serveur si elle n'existe pas
            if server_id not in self.xp_data:
                self.xp_data[server_id] = {}
                print(f"[XP] [Server:{server_id}] Nouvelle structure de données XP créée")
            
            # Initialise l'utilisateur dans le serveur s'il n'existe pas
            if user_id not in self.xp_data[server_id]:
                self.xp_data[server_id][user_id] = {"xp": 0, "level": 1}
                print(f"[XP] [Server:{server_id}] [User:{user_id}] Initialisation XP")
            
            # Ajoute l'XP et vérifie le niveau
            old_xp = self.xp_data[server_id][user_id]["xp"]
            self.xp_data[server_id][user_id]["xp"] += xp_amount
            new_level = self.calculate_level(self.xp_data[server_id][user_id]["xp"])
            
            print(f"[XP] [Server:{server_id}] [User:{user_id}] +{xp_amount}XP ({old_xp}->{self.xp_data[server_id][user_id]['xp']})")
            
            if new_level > self.xp_data[server_id][user_id]["level"]:
                old_level = self.xp_data[server_id][user_id]["level"]
                self.xp_data[server_id][user_id]["level"] = new_level
                print(f"[XP] [Server:{server_id}] [User:{user_id}] Level {old_level}->{new_level}")
                await self.notify_level_up(user_id, server_id)
                
            self.save_xp_data()  # Suppression du await
            
        except Exception as e:
            print(f"[XP] [ERROR] [Server:{server_id}] [User:{user_id}] Erreur add_xp: {str(e)}")
            raise

    async def notify_level_up(self, user_id, server_id):
        try:
            # Récupère l'ID du canal pour ce serveur
            channel_id = self.level_up_channels.get(server_id)
            if not channel_id:
                print(f"[XP] [Server:{server_id}] Pas de canal level up configuré")
                return

            channel = self.bot.get_channel(channel_id)
            if channel is None:
                print(f"[XP] [Server:{server_id}] [User:{user_id}] Canal {channel_id} introuvable")
                return

            user = self.bot.get_user(int(user_id))
            if user is None:
                try:
                    user = await self.bot.fetch_user(int(user_id))
                except discord.NotFound:
                    print(f"[XP] [Server:{server_id}] [User:{user_id}] Utilisateur introuvable")
                    return
                except discord.HTTPException as e:
                    print(f"[XP] [Server:{server_id}] [User:{user_id}] HTTPException: {str(e)}")
                    return

            if user:
                try:
                    new_level = self.xp_data[server_id][str(user_id)]['level']
                    await channel.send(f"Congratulations {user}! You have reached the level {new_level}!")
                    print(f"[XP] [Server:{server_id}] [User:{user_id}] Notification level {new_level} envoyée")
                except discord.Forbidden:
                    print(f"[XP] [Server:{server_id}] [User:{user_id}] Impossible d'envoyer au canal {channel_id}")
        
        except Exception as e:
            print(f"[XP] [ERROR] [Server:{server_id}] [User:{user_id}] Erreur notify_level_up: {str(e)}")

    @commands.Cog.listener()
    async def on_message(self, message):
        """Gestionnaire d'événements pour les messages"""
        # Ignore les messages du bot
        if message.author.bot:
            return
        
        # Ignore les messages privés (DM)
        if not message.guild:
            return
        
        # Ajoute l'XP seulement pour les messages dans les serveurs
        await self.add_xp(message.author.id, message.guild.id, 10)

    @commands.command(name="resetxp")
    @commands.has_permissions(administrator=True)
    async def reset_xp(self, ctx: Context, member: discord.Member):
        server_id = str(ctx.guild.id)
        user_id = str(member.id)
        
        if server_id in self.xp_data and user_id in self.xp_data[server_id]:
            self.xp_data[server_id][user_id] = {"xp": 0, "level": 1}
            self.save_xp_data()
            await ctx.send(f"L'XP de {member.name} a été réinitialisée.")
        else:
            await ctx.send(f"{member.name} n'a pas d'XP à réinitialiser.")

    @commands.command(name='xp', help='Affiche votre nombre d\'XP actuel')
    async def check_xp(self, ctx):
        server_id = str(ctx.guild.id)
        user_id = str(ctx.author.id)
        
        if server_id in self.xp_data and user_id in self.xp_data[server_id]:
            xp = self.xp_data[server_id][user_id]["xp"]
            level = self.xp_data[server_id][user_id]["level"]
        else:
            xp = 0
            level = 1

        embed = discord.Embed(title="Your XP Profile", color=0x00ff00)
        embed.set_thumbnail(url=ctx.author.avatar.url)
        embed.add_field(name="Server", value=ctx.guild.name, inline=False)
        embed.add_field(name="User", value=ctx.author.display_name, inline=False)
        embed.add_field(name="Level", value=str(level), inline=True)
        embed.add_field(name="XP", value=str(xp), inline=True)

        await ctx.send(embed=embed)

    @commands.command(name='leaderboard', help='Displays the server XP ranking')
    async def leaderboard(self, ctx):
        server_id = str(ctx.guild.id)
        
        if server_id not in self.xp_data:
            await ctx.send("No XP data exists for this server!")
            return
            
        # Trie les utilisateurs par XP
        sorted_users = sorted(
            self.xp_data[server_id].items(),
            key=lambda x: x[1]["xp"],
            reverse=True
        )[:10]  # Top 10

        embed = discord.Embed(title=f"Leadboard XP - {ctx.guild.name}", color=0x00ff00)
        
        for rank, (user_id, data) in enumerate(sorted_users, 1):
            user = ctx.guild.get_member(int(user_id))
            if user:
                embed.add_field(
                    name=f"#{rank} {user.display_name}",
                    value=f"Level: {data['level']} | XP: {data['xp']}",
                    inline=False
                )

        await ctx.send(embed=embed)

    # Commande pour configurer le canal de level up
    @commands.command(name="setlevelup")
    @commands.has_permissions(administrator=True)
    async def set_level_up_channel(self, ctx, channel: discord.TextChannel = None):
        """Configure le canal pour les notifications de level up"""
        channel = channel or ctx.channel
        server_id = str(ctx.guild.id)
        
        self.level_up_channels[server_id] = channel.id
        await ctx.send(f"Canal de level up configuré sur {channel.mention}")

async def setup(bot):
    await bot.add_cog(XP(bot))