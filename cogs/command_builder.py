import discord
from discord.ext import commands
import json
import os
import asyncio

class CommandBuilder(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.commands = self.load_commands()

    def load_commands(self):
        if os.path.exists("commands.json"):
            with open("commands.json", "r") as file:
                return json.load(file)
        return {}

    def save_commands(self):
        with open("commands.json", "w") as file:
            json.dump(self.commands, file, indent=4)

    @commands.command(name="create_command")
    async def create_command(self, ctx):
        def check(m):
            return m.author == ctx.author and m.channel == ctx.channel

        await ctx.send("Please enter the name of the new command:")
        try:
            name_msg = await self.bot.wait_for("message", check=check, timeout=60)
            command_name = name_msg.content

            await ctx.send("Please enter the response of the new command:")
            response_msg = await self.bot.wait_for("message", check=check, timeout=60)
            command_response = response_msg.content

            # Ajouter la nouvelle commande au dictionnaire des commandes
            self.commands[command_name] = command_response
            self.save_commands()

            await ctx.send(f"Command `{command_name}` has been created successfully!")

        except asyncio.TimeoutError:
            await ctx.send("You took too long to respond. Please try again.")

    @commands.Cog.listener()
    async def on_ready(self):
        for command_name, command_response in self.commands.items():
            async def dynamic_command(ctx, response=command_response):
                await ctx.send(response)

            self.bot.command(name=command_name)(dynamic_command)

        print(f"CommandBuilder loaded and ready.")

async def setup(bot):
    await bot.add_cog(CommandBuilder(bot))