import discord
from discord.ext import commands
from discord.ext.commands import Context
import json
import os
import math

# Replace with your specific channel ID
LEVEL_UP_CHANNEL_ID = 1104041737850196019  # Replace with your channel ID

class XP(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.xp_data = self.load_xp_data()

    def load_xp_data(self):
        if os.path.exists("xp_data.json"):
            try:
                with open("xp_data.json", "r") as f:
                    data = json.load(f)
                print("XP data loaded successfully.")
                return data
            except json.JSONDecodeError:
                print("Error: xp_data.json is not a valid JSON. Initializing empty XP data.")
                return {}
            except Exception as e:
                print(f"Unexpected error while loading XP data: {e}")
                return {}
        else:
            print("xp_data.json not found. Initializing empty XP data.")
            return {}

    def save_xp_data(self):
        try:
            with open("xp_data.json", "w") as f:
                json.dump(self.xp_data, f, indent=4)
            print("XP data saved successfully.")
        except Exception as e:
            print(f"Error saving XP data: {e}")

    def calculate_level(self, xp):
        return math.floor(xp / 300) + 1  # Example: 100 XP per level

    async def add_xp(self, user_id, xp_amount):
        print(f"Adding {xp_amount} XP to user ID {user_id}")
        if user_id in self.xp_data:
            self.xp_data[user_id]["xp"] += xp_amount
            new_level = self.calculate_level(self.xp_data[user_id]["xp"])
            if new_level > self.xp_data[user_id]["level"]:
                self.xp_data[user_id]["level"] = new_level
                await self.notify_level_up(user_id)
            print(f"User {user_id} now has {self.xp_data[user_id]['xp']} XP and is level {self.xp_data[user_id]['level']}")
        else:
            calculated_level = self.calculate_level(xp_amount)
            self.xp_data[user_id] = {"xp": xp_amount, "level": calculated_level}
            print(f"User {user_id} added with {xp_amount} XP and level {calculated_level}")
        self.save_xp_data()

    async def notify_level_up(self, user_id):
        channel = self.bot.get_channel(LEVEL_UP_CHANNEL_ID)
        if channel is None:
            print(f"Channel with ID {LEVEL_UP_CHANNEL_ID} not found.")
            return

        user = self.bot.get_user(user_id)
        if user is None:
            try:
                user = await self.bot.fetch_user(user_id)
            except discord.NotFound:
                print(f"User with ID {user_id} not found.")
                return
            except discord.HTTPException as e:
                print(f"HTTPException while fetching user with ID {user_id}: {e}")
                return

        if user:
            try:
                await channel.send(f"Félicitations {user}! Vous avez atteint le niveau {self.xp_data[user_id]['level']}!")
                print(f"Level up message sent to {user.name} in channel ID {LEVEL_UP_CHANNEL_ID}")
            except discord.Forbidden:
                print(f"Cannot send message to channel ID {LEVEL_UP_CHANNEL_ID}.")

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot:
            return

        await self.add_xp(str(message.author.id), 10)  # Ensure user_id is a string

    @commands.command(name="getxp")
    async def get_xp(self, ctx):
        user_id = str(ctx.author.id)
        if user_id in self.xp_data:
            xp = self.xp_data[user_id]["xp"]
            level = self.xp_data[user_id]["level"]
            await ctx.send(f"Vous avez {xp} XP et vous êtes au niveau {level}.")
        else:
            await ctx.send("Vous n'avez pas encore de XP.")

    @commands.command(name="resetxp")
    @commands.has_permissions(administrator=True)
    async def reset_xp(self, ctx: Context, member: discord.Member):
        user_id = str(member.id)
        if user_id in self.xp_data:
            self.xp_data[user_id] = {"xp": 0, "level": 1}
            self.save_xp_data()
            await ctx.send(f"{member.name}'s XP has been reset.")
        else:
            await ctx.send(f"{member.name} has no XP to reset.")

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