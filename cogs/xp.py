import discord
from discord.ext import commands
from discord.ext.commands import Context
import json
import os
import math

# Remplacez par l'ID de votre canal spécifique
LEVEL_UP_CHANNEL_ID = 1104041737850196019  # Remplacez par l'ID de votre canal

class XP(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.xp_data = self.load_xp_data()

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

    def save_xp_data(self):
        try:
            with open("xp_data.json", "w") as f:
                json.dump(self.xp_data, f, indent=4)
            print("Données XP sauvegardées avec succès.")
        except Exception as e:
            print(f"Erreur lors de la sauvegarde des données XP : {e}")

    def calculate_level(self, xp):
        return math.floor(xp / 300) + 1  # Exemple : 300 XP par niveau

    async def add_xp(self, user_id, xp_amount):
        print(f"Ajout de {xp_amount} XP à l'utilisateur ID {user_id}")
        if user_id in self.xp_data:
            self.xp_data[user_id]["xp"] += xp_amount
            new_level = self.calculate_level(self.xp_data[user_id]["xp"])
            if new_level > self.xp_data[user_id]["level"]:
                self.xp_data[user_id]["level"] = new_level
                await self.notify_level_up(user_id)
            print(f"L'utilisateur {user_id} a maintenant {self.xp_data[user_id]['xp']} XP et est niveau {self.xp_data[user_id]['level']}")
        else:
            calculated_level = self.calculate_level(xp_amount)
            self.xp_data[user_id] = {"xp": xp_amount, "level": calculated_level}
            print(f"L'utilisateur {user_id} ajouté avec {xp_amount} XP et niveau {calculated_level}")
        self.save_xp_data()

    async def notify_level_up(self, user_id):
        channel = self.bot.get_channel(LEVEL_UP_CHANNEL_ID)
        if channel is None:
            print(f"Canal avec l'ID {LEVEL_UP_CHANNEL_ID} introuvable.")
            return

        user = self.bot.get_user(int(user_id))
        if user is None:
            try:
                user = await self.bot.fetch_user(int(user_id))
            except discord.NotFound:
                print(f"Utilisateur avec l'ID {user_id} introuvable.")
                return
            except discord.HTTPException as e:
                print(f"HTTPException lors de la récupération de l'utilisateur avec l'ID {user_id} : {e}")
                return

        if user:
            try:
                await channel.send(f"Félicitations {user}! Vous avez atteint le niveau {self.xp_data[user_id]['level']}!")
                print(f"Message de montée en niveau envoyé à {user.name} dans le canal ID {LEVEL_UP_CHANNEL_ID}")
            except discord.Forbidden:
                print(f"Impossible d'envoyer un message au canal ID {LEVEL_UP_CHANNEL_ID}.")

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot:
            return

        await self.add_xp(str(message.author.id), 10)  # Assurez-vous que user_id est une chaîne

    @commands.command(name="resetxp")
    @commands.has_permissions(administrator=True)
    async def reset_xp(self, ctx: Context, member: discord.Member):
        user_id = str(member.id)
        if user_id in self.xp_data:
            self.xp_data[user_id] = {"xp": 0, "level": 1}
            self.save_xp_data()
            await ctx.send(f"L'XP de {member.name} a été réinitialisée.")
        else:
            await ctx.send(f"{member.name} n'a pas d'XP à réinitialiser.")

    @commands.command(name='xp', help='Affiche votre nombre d\'XP actuel')
    async def check_xp(self, ctx):
        user_id = str(ctx.author.id)
        if user_id in self.xp_data:
            xp = self.xp_data[user_id]["xp"]
            level = self.xp_data[user_id]["level"]
        else:
            xp = 0
            level = 1

        embed = discord.Embed(title="Votre Profil XP", color=0x00ff00)
        embed.set_thumbnail(url=ctx.author.avatar.url)
        embed.add_field(name="Utilisateur", value=ctx.author.display_name, inline=False)
        embed.add_field(name="Niveau", value=str(level), inline=True)
        embed.add_field(name="XP", value=str(xp), inline=True)

        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(XP(bot))