import discord
from discord.ext import commands
import json
import os
import asyncio

class CommandBuilder(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.commands_data = self.load_commands()
        self.fix_commands_format()
        self.register_all_commands()

    def load_commands(self):
        """Charge les commandes depuis le fichier commands.json."""
        if os.path.exists("commands.json"):
            with open("commands.json", "r", encoding="utf-8") as file:
                data = json.load(file)
                # Conversion de l'ancien format vers le nouveau si nécessaire
                if not isinstance(data, dict) or ("global" not in data and "servers" not in data):
                    return {"global": data, "servers": {}}
                return data
        return {"global": {}, "servers": {}}

    def save_commands(self):
        """Sauvegarde les commandes dans le fichier commands.json."""
        with open("commands.json", "w", encoding="utf-8") as file:
            json.dump(self.commands_data, file, indent=4, ensure_ascii=False)

    def fix_commands_format(self):
        """Met à jour le format des commandes dans commands.json pour assurer une structure cohérente."""
        modified = False

        # Correction des commandes globales
        if "global" in self.commands_data:
            for cmd_name, cmd_content in list(self.commands_data["global"].items()):
                if not isinstance(cmd_content, dict):
                    self.commands_data["global"][cmd_name] = {
                        "response": cmd_content,
                        "description": f"Command {cmd_name}"
                    }
                    modified = True
                    print(f"[FORMAT] Commande globale '{cmd_name}' mise à jour")

        # Correction des commandes par serveur
        if "servers" in self.commands_data:
            for server_id, server_commands in self.commands_data["servers"].items():
                for cmd_name, cmd_content in list(server_commands.items()):
                    if not isinstance(cmd_content, dict):
                        self.commands_data["servers"][server_id][cmd_name] = {
                            "response": cmd_content,
                            "description": f"Command {cmd_name}"
                        }
                        modified = True
                        print(f"[FORMAT] Commande '{cmd_name}' du serveur {server_id} mise à jour")

        # Sauvegarde si des modifications ont été effectuées
        if modified:
            self.save_commands()
            print("[FORMAT] Fichier commands.json mis à jour avec succès")

    def register_all_commands(self):
        """Enregistre toutes les commandes existantes lors de l'initialisation du Cog."""
        # Enregistre les commandes globales
        for command_name, command_response in self.commands_data.get("global", {}).items():
            self.register_command(command_name, command_response, is_global=True)
        
        # Enregistre les commandes par serveur
        for server_id, commands in self.commands_data.get("servers", {}).items():
            for command_name, command_response in commands.items():
                self.register_command(command_name, command_response, is_global=False, server_id=server_id)

    def register_command(self, command_name, command_data, is_global=True, server_id=None):
        """Enregistre une commande personnalisée dynamiquement."""
        # Ne pas enregistrer les commandes intégrées du cog
        if command_name in ['list_commands', 'commands', 'cmds', 'create_command']:
            return

        if not self.bot.get_command(command_name):
            async def dynamic_command(ctx):
                # Vérifie si la commande est accessible dans ce serveur
                current_server = str(ctx.guild.id)
                
                # Vérifie d'abord si c'est une commande globale
                if is_global:
                    await ctx.send(command_data.get('response', command_data))
                    return
                    
                # Vérifie ensuite si la commande existe pour ce serveur
                if current_server in self.commands_data.get("servers", {}) and command_name in self.commands_data["servers"][current_server]:
                    command_content = self.commands_data["servers"][current_server][command_name]
                    await ctx.send(command_content.get('response', command_content))
                else:
                    await ctx.send("This command is not available on this server.")
                    
            dynamic_command.__name__ = f"dynamic_command_{command_name}"
            self.bot.command(name=command_name, description=command_data.get('description', "Commande personnalisée"))(dynamic_command)
            print(f"[COMMAND] Commande `{command_name}` enregistrée {'(globale)' if is_global else f'(serveur {server_id})'}")

    @commands.command(name="create_command", description="Create a custom command.")
    @commands.has_permissions(administrator=True)
    async def create_command(self, ctx):
        """Commande pour créer une nouvelle commande personnalisée."""
        def check(m):
            return m.author == ctx.author and m.channel == ctx.channel

        await ctx.send("Do you want to create a global (G) or server-specific (S) command? If you dont know, Write 'S'")
        try:
            type_msg = await self.bot.wait_for("message", check=check, timeout=60)
            is_global = type_msg.content.upper() == "G"

            await ctx.send("Please enter the name of the new command :")
            name_msg = await self.bot.wait_for("message", check=check, timeout=60)
            command_name = name_msg.content.strip().lower()

            if not command_name.isalnum():
                await ctx.send("Command name must be alphanumeric without spaces.")
                return

            # Nouvelle vérification pour les commandes existantes
            current_server_id = str(ctx.guild.id)
            command_exists = False

            # Vérifie dans les commandes globales
            if command_name in self.commands_data.get("global", {}):
                command_exists = True

            # Vérifie dans les commandes du serveur actuel
            if (current_server_id in self.commands_data.get("servers", {}) and 
                command_name in self.commands_data["servers"][current_server_id]):
                command_exists = True

            if command_exists:
                await ctx.send(f"A command named `{command_name}` already exists on this server or globally.")
                return

            await ctx.send("Please enter a short description for the order :")
            desc_msg = await self.bot.wait_for("message", check=check, timeout=60)
            command_description = desc_msg.content.strip()

            await ctx.send("Please enter the answer to the new command :")
            response_msg = await self.bot.wait_for("message", check=check, timeout=60)
            command_response = response_msg.content.strip()

            # Structure de la nouvelle commande
            command_data = {
                "response": command_response,
                "description": command_description
            }

            # Ajoute la nouvelle commande avec le bon format
            if is_global:
                if "global" not in self.commands_data:
                    self.commands_data["global"] = {}
                self.commands_data["global"][command_name] = command_data
            else:
                server_id = str(ctx.guild.id)
                if "servers" not in self.commands_data:
                    self.commands_data["servers"] = {}
                if server_id not in self.commands_data["servers"]:
                    self.commands_data["servers"][server_id] = {}
                self.commands_data["servers"][server_id][command_name] = command_data

            self.save_commands()
            self.register_command(command_name, command_data, is_global, str(ctx.guild.id) if not is_global else None)
            
            await ctx.send(f"The command `{command_name}` has been successfully created !")

        except asyncio.TimeoutError:
            await ctx.send("You took too long to reply. Please try again.")

    @commands.command(name="list_commands", aliases=["commands", "cmds"])
    async def list_commands(self, ctx):
        """Liste toutes les commandes disponibles avec leurs descriptions."""
        
        def create_embed(title, commands_dict, page_num=1, max_per_page=10):
            embed = discord.Embed(
                title=f"📜 {title}",
                color=discord.Color.blue()
            )

            # Convertir le dictionnaire en liste pour la pagination
            commands_list = list(commands_dict.items())
            start_idx = (page_num - 1) * max_per_page
            end_idx = min(start_idx + max_per_page, len(commands_list))
            
            commands_text = ""
            for cmd_name, cmd_data in commands_list[start_idx:end_idx]:
                if isinstance(cmd_data, dict):
                    description = cmd_data.get('description', 'Pas de description')
                else:
                    description = str(cmd_data)[:50] + "..." if len(str(cmd_data)) > 50 else str(cmd_data)
                commands_text += f"**!{cmd_name}**\n→ {description}\n\n"

            if commands_text:
                embed.add_field(name="\u200b", value=commands_text, inline=False)
            else:
                embed.add_field(name="\u200b", value="Aucune commande disponible", inline=False)

            total_pages = (len(commands_list) + max_per_page - 1) // max_per_page
            embed.set_footer(text=f"Page {page_num}/{total_pages} • Use !create_command to create a command")
            return embed, total_pages

        # Commandes globales
        global_commands = self.commands_data.get("global", {})
        if global_commands:
            current_page = 1
            embed, total_pages = create_embed("Commandes Globales", global_commands, current_page)
            global_message = await ctx.send(embed=embed)
            
            if total_pages > 1:
                await global_message.add_reaction("◀️")
                await global_message.add_reaction("▶️")

        # Commandes du serveur
        server_id = str(ctx.guild.id)
        if server_id in self.commands_data.get("servers", {}):
            server_commands = self.commands_data["servers"][server_id]
            current_page = 1
            embed, total_pages = create_embed(f"Commands of {ctx.guild.name}", server_commands, current_page)
            server_message = await ctx.send(embed=embed)
            
            if total_pages > 1:
                await server_message.add_reaction("◀️")
                await server_message.add_reaction("▶️")

        def check(reaction, user):
            return user == ctx.author and str(reaction.emoji) in ["◀️", "▶️"]

        # Gestion des réactions pour la pagination
        while True:
            try:
                reaction, user = await self.bot.wait_for("reaction_add", timeout=60.0, check=check)

                if str(reaction.emoji) == "▶️" and current_page < total_pages:
                    current_page += 1
                elif str(reaction.emoji) == "◀️" and current_page > 1:
                    current_page -= 1
                else:
                    await reaction.remove(user)
                    continue

                # Met à jour l'embed avec la nouvelle page
                if reaction.message.id == global_message.id:
                    embed, _ = create_embed("Commandes Globales", global_commands, current_page)
                    await global_message.edit(embed=embed)
                else:
                    embed, _ = create_embed(f"Commands of {ctx.guild.name}", server_commands, current_page)
                    await server_message.edit(embed=embed)

                await reaction.remove(user)

            except asyncio.TimeoutError:
                break

    @commands.Cog.listener()
    async def on_ready(self):
        print(f"CommandBuilder chargé et prêt.")

async def setup(bot):
    await bot.add_cog(CommandBuilder(bot))