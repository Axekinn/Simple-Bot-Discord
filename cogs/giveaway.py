import asyncio
import json
import os
import datetime
import random
import discord
from discord.ext import commands
from discord.ext.commands import Context

class Giveaway(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.giveaways = self.load_giveaways()
        self.schedule_giveaways()  # Planifier les giveaways au démarrage

    def load_giveaways(self):
        if os.path.exists("giveaways.json"):
            try:
                with open("giveaways.json", "r") as f:
                    data = json.load(f)
                print("Giveaways chargés avec succès.")
                return data
            except json.JSONDecodeError:
                print("Error: giveaways.json is not a valid JSON. Empty giveaways initialization.")
                return []
            except Exception as e:
                print(f"Unexpected error when loading giveaways : {e}")
                return []
        else:
            print("giveaways.json not found. Initialization of empty giveaways.")
            return []

    def save_giveaways(self):
        try:
            with open("giveaways.json", "w") as f:
                json.dump(self.giveaways, f, indent=4)
            print("Giveaways successfully saved.")
        except Exception as e:
            print(f"Error saving giveaways: {e}")

    def schedule_giveaways(self):
        current_time = datetime.datetime.utcnow().timestamp()
        for giveaway in self.giveaways:
            end_time = giveaway["end_time"]
            remaining_time = end_time - current_time
            if remaining_time > 0:
                # Planifier la fin du giveaway après le temps restant
                asyncio.create_task(self.end_giveaway_after_delay(giveaway["message_id"], remaining_time))
            else:
                # Si le temps est écoulé, terminer le giveaway immédiatement
                asyncio.create_task(self.end_giveaway(giveaway["message_id"]))

    async def end_giveaway_after_delay(self, message_id: int, delay: float):
        await asyncio.sleep(delay)
        await self.end_giveaway(message_id)

    async def end_giveaway(self, message_id: int) -> None:
        giveaway = next((g for g in self.giveaways if g["message_id"] == message_id), None)
        if not giveaway:
            return

        # Retirer le giveaway de la liste et sauvegarder
        self.giveaways = [g for g in self.giveaways if g["message_id"] != message_id]
        self.save_giveaways()

        channel = self.bot.get_channel(giveaway["channel_id"])
        if channel is None:
            return

        try:
            message = await channel.fetch_message(giveaway["message_id"])
        except discord.NotFound:
            return

        users = [user async for user in message.reactions[0].users() if not user.bot]

        if len(users) == 0:
            await channel.send("No one participated in the giveaway.")
            return

        winners = random.sample(users, min(giveaway["winners"], len(users)))
        winner_mentions = ", ".join([winner.mention for winner in winners])
        await channel.send(f"Congratulations {winner_mentions} ! You've won **{giveaway['prize']}** !")

    def parse_duration(self, duration: str) -> int:
        unit = duration[-1]
        if unit not in "smhd":
            raise ValueError("Invalid time unit. Use 's' for seconds, 'm' for minutes, 'h' for hours or 'd' for days.")
        try:
            value = int(duration[:-1])
        except ValueError:
            raise ValueError("Invalid duration value.")

        if unit == "s":
            return value
        elif unit == "m":
            return value * 60
        elif unit == "h":
            return value * 3600
        elif unit == "d":
            return value * 86400

    @commands.command(name="start_giveaway", description="Start a giveaway")
    async def start_giveaway(self, ctx: Context, duration: str, winners: int, *, prize: str) -> None:
        """
        Démarrer un giveaway.
        :param ctx: Le contexte de la commande.
        :param duration: La durée du giveaway (par ex., '10s', '5m', '1h', '2d').
        :param winners: Le nombre de gagnants.
        :param prize: Le prix du giveaway.
        """
        try:
            duration_seconds = self.parse_duration(duration)
        except ValueError as e:
            await ctx.send(str(e))
            return

        end_time = (datetime.datetime.utcnow() + datetime.timedelta(seconds=duration_seconds)).timestamp()
        end_timestamp = int(end_time)
        embed = discord.Embed(
            title="🎉 Giveaway ! 🎉",
            description=f"Prize : {prize}\nReact with 🎉 to participate !\nEnds on : <t:{end_timestamp}:f>\nNumber of winners : {winners}",
            color=0xBEBEFE,
        )
        message = await ctx.send(embed=embed)
        await message.add_reaction("🎉")

        self.giveaways.append({
            "message_id": message.id,
            "channel_id": ctx.channel.id,
            "prize": prize,
            "winners": winners,
            "end_time": end_time
        })
        self.save_giveaways()

        # Planifier la fin du giveaway sans bloquer
        asyncio.create_task(self.end_giveaway_after_delay(message.id, duration_seconds))

    @commands.command(name="reroll", description="Relaunching a giveaway")
    async def reroll_giveaway(self, ctx: Context, message_id: int) -> None:
        """
        Relancer un giveaway.
        :param ctx: Le contexte de la commande.
        :param message_id: L'ID du message du giveaway.
        """
        channel = ctx.channel
        try:
            message = await channel.fetch_message(message_id)
        except discord.NotFound:
            await ctx.send("Message not found.")
            return

        users = [user async for user in message.reactions[0].users() if not user.bot]

        if len(users) == 0:
            await ctx.send("No one participated in the giveaway.")
            return

        winner = random.choice(users)
        await channel.send(f"Congratulations {winner.mention} ! You have won the giveaway reroll !")

async def setup(bot):
    await bot.add_cog(Giveaway(bot))