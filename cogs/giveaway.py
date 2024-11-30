import discord
from discord.ext import commands, tasks
from discord.ext.commands import Context
import asyncio
import random
import os

class Giveaway(commands.Cog, name="giveaway"):
    def __init__(self, bot) -> None:
        self.bot = bot
        self.giveaways = []

    @commands.command(name="giveaway", description="Start a giveaway")
    async def start_giveaway(self, ctx: Context, duration: int, winners: int, *, prize: str) -> None:
        """
        Start a giveaway.
        :param ctx: The context of the command.
        :param duration: The duration of the giveaway in seconds.
        :param winners: The number of winners.
        :param prize: The prize of the giveaway.
        """
        embed = discord.Embed(
            title="🎉 Giveaway! 🎉",
            description=f"Prize: {prize}\nReact with 🎉 to enter!\nDuration: {duration} seconds\nWinners: {winners}",
            color=0xBEBEFE,
        )
        message = await ctx.send(embed=embed)
        await message.add_reaction("🎉")

        self.giveaways.append({
            "message_id": message.id,
            "channel_id": ctx.channel.id,
            "prize": prize,
            "winners": winners,
            "end_time": discord.utils.utcnow().timestamp() + duration
        })

        await asyncio.sleep(duration)
        await self.end_giveaway(message.id)

    async def end_giveaway(self, message_id: int) -> None:
        giveaway = next((g for g in self.giveaways if g["message_id"] == message_id), None)
        if not giveaway:
            return

        channel = self.bot.get_channel(giveaway["channel_id"])
        message = await channel.fetch_message(giveaway["message_id"])
        users = []
        async for user in message.reactions[0].users():
            if not user.bot:
                users.append(user)

        if len(users) == 0:
            await channel.send("No one entered the giveaway.")
            return

        winners = random.sample(users, min(giveaway["winners"], len(users)))
        winner_mentions = ", ".join([winner.mention for winner in winners])
        await channel.send(f"Congratulations {winner_mentions}! You won the giveaway for **{giveaway['prize']}**!")

    @commands.command(name="reroll_giveaway", description="Reroll a giveaway")
    async def reroll_giveaway(self, ctx: Context, message_id: int) -> None:
        """
        Reroll a giveaway.
        :param ctx: The context of the command.
        :param message_id: The ID of the giveaway message.
        """
        giveaway = next((g for g in self.giveaways if g["message_id"] == message_id), None)
        if not giveaway:
            await ctx.send("Giveaway not found.")
            return

        channel = self.bot.get_channel(giveaway["channel_id"])
        message = await channel.fetch_message(giveaway["message_id"])
        users = await message.reactions[0].users().flatten()
        users = [user for user in users if not user.bot]

        if len(users) == 0:
            await ctx.send("No one entered the giveaway.")
            return

        winners = random.sample(users, min(giveaway["winners"], len(users)))
        winner_mentions = ", ".join([winner.mention for winner in winners])

        embed = discord.Embed(
            title="🎉 Giveaway Rerolled! 🎉",
            description=f"Prize: {giveaway['prize']}\nNew Winners: {winner_mentions}",
            color=0xBEBEFE,
        )
        await channel.send(embed=embed)

    async def load_cogs(self) -> None:
        """
        The code in this function is executed whenever the bot will start.
        """
        for filename in os.listdir('./cogs'):
            if filename.endswith('.py'):
                await self.load_extension(f'cogs.{filename[:-3]}')

async def setup(bot):
    await bot.add_cog(Giveaway(bot))