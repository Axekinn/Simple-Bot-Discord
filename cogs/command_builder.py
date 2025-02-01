import discord
from discord.ext import commands
import json
import os
import asyncio

class CommandBuilder(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.commands_data = self.load_commands()
        self.register_all_commands()

    def load_commands(self):
        """Charge les commandes depuis le fichier commands.json."""
        if os.path.exists("commands.json"):
            with open("commands.json", "r", encoding="utf-8") as file:
                return json.load(file)
        return {}

    def save_commands(self):
        """Sauvegarde les commandes dans le fichier commands.json."""
        with open("commands.json", "w", encoding="utf-8") as file:
            json.dump(self.commands_data, file, indent=4, ensure_ascii=False)

    def register_all_commands(self):
        """Enregistre toutes les commandes existantes lors de l'initialisation du Cog."""
        for command_name, command_response in self.commands_data.items():
            self.register_command(command_name, command_response)

    def register_command(self, command_name, command_response):
        """Enregistre une commande personnalisée dynamiquement."""
        if not self.bot.get_command(command_name):
            async def dynamic_command(ctx):
                await ctx.send(command_response)
            dynamic_command.__name__ = f"dynamic_command_{command_name}"
            self.bot.command(name=command_name, description="Customized command.")(dynamic_command)
            print(f"Commande `{command_name}` enregistrée.")

    @commands.command(name="create_command", description="Create a custom command.")
    @commands.has_permissions(administrator=True)
    async def create_command(self, ctx):
        """Commande pour créer une nouvelle commande personnalisée."""
        def check(m):
            return m.author == ctx.author and m.channel == ctx.channel

        await ctx.send("Please enter the name of the new order:")
        try:
            name_msg = await self.bot.wait_for("message", check=check, timeout=60)
            command_name = name_msg.content.strip()

            if not command_name.isalnum():
                await ctx.send("The order name must be alphanumeric with no spaces.")
                return

            if command_name in self.commands_data or self.bot.get_command(command_name):
                await ctx.send(f"A command named `{command_name}` already exists.")
                return

            await ctx.send("Please enter the new command response:")
            response_msg = await self.bot.wait_for("message", check=check, timeout=60)
            command_response = response_msg.content.strip()

            # Ajouter la nouvelle commande au dictionnaire des commandes
            self.commands_data[command_name] = command_response
            self.save_commands()

            # Enregistrer la nouvelle commande dynamiquement
            self.register_command(command_name, command_response)

            await ctx.send(f"Command `{command_name}` has been successfully created!")

        except asyncio.TimeoutError:
            await ctx.send("You took too long to reply. Please try again.")

    @commands.Cog.listener()
    async def on_ready(self):
        print(f"CommandBuilder chargé et prêt.")

async def setup(bot):
    await bot.add_cog(CommandBuilder(bot))