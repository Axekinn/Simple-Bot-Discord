import discord
from discord.ext import commands
from discord.ui import View, Button, Select
from discord import app_commands
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
        if command_name in ['list_commands', 'commands', 'cmds', 'create_command', 'edit_command']:
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

    @commands.hybrid_command(
        name="create_command",
        description="Create a custom command for your server or globally."
    )
    @app_commands.default_permissions(administrator=True)
    @commands.has_permissions(administrator=True)
    async def create_command(self, ctx):
        """Create a new custom command with an interactive interface."""
        # Répondre immédiatement pour éviter les erreurs d'interaction
        if ctx.interaction:
            await ctx.defer()
            
        # Reste du code inchangé...

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

        # Initialiser les variables pour le suivi des messages
        paginated_messages = {}
        current_pages = {}

        # Commandes globales
        global_commands = self.commands_data.get("global", {})
        if global_commands:
            current_pages["global"] = 1
            embed, total_pages = create_embed("Global Commands", global_commands, current_pages["global"])
            global_message = await ctx.send(embed=embed)
            paginated_messages["global"] = {"message": global_message, "commands": global_commands, "total_pages": total_pages}
            
            if total_pages > 1:
                await global_message.add_reaction("◀️")
                await global_message.add_reaction("▶️")

        # Commandes du serveur
        server_id = str(ctx.guild.id)
        if server_id in self.commands_data.get("servers", {}) and self.commands_data["servers"][server_id]:
            server_commands = self.commands_data["servers"][server_id]
            current_pages["server"] = 1
            embed, total_pages = create_embed(f"Commands of {ctx.guild.name}", server_commands, current_pages["server"])
            server_message = await ctx.send(embed=embed)
            paginated_messages["server"] = {"message": server_message, "commands": server_commands, "total_pages": total_pages}
            
            if total_pages > 1:
                await server_message.add_reaction("◀️")
                await server_message.add_reaction("▶️")

        # Si aucune commande n'est disponible, informer l'utilisateur
        if not paginated_messages:
            await ctx.send("No custom commands available. Use `!create_command` to create one!")
            return

        def check(reaction, user):
            # Vérifie que la réaction est sur un message que nous surveillons
            return (user == ctx.author and 
                    str(reaction.emoji) in ["◀️", "▶️"] and
                    any(reaction.message.id == data["message"].id for data in paginated_messages.values()))

        # Gestion des réactions pour la pagination
        while True:
            try:
                reaction, user = await self.bot.wait_for("reaction_add", timeout=60.0, check=check)

                # Déterminer quel message a été réagi
                message_type = None
                for msg_type, data in paginated_messages.items():
                    if reaction.message.id == data["message"].id:
                        message_type = msg_type
                        break

                if not message_type:
                    continue

                # Mettre à jour la page
                if str(reaction.emoji) == "▶️" and current_pages[message_type] < paginated_messages[message_type]["total_pages"]:
                    current_pages[message_type] += 1
                elif str(reaction.emoji) == "◀️" and current_pages[message_type] > 1:
                    current_pages[message_type] -= 1
                else:
                    await reaction.remove(user)
                    continue

                # Met à jour l'embed avec la nouvelle page
                title = "Global Commands" if message_type == "global" else f"Commands of {ctx.guild.name}"
                embed, _ = create_embed(title, paginated_messages[message_type]["commands"], current_pages[message_type])
                await paginated_messages[message_type]["message"].edit(embed=embed)

                await reaction.remove(user)

            except asyncio.TimeoutError:
                # Fin de la pagination après un délai d'inactivité
                break
            except Exception as e:
                print(f"Error in pagination: {e}")
                break

    def create_command_info_embed(self, cmd_name, cmd_data, message):
        """Creates an embed with command information."""
        embed = discord.Embed(
            title=f"Command: {cmd_name}",
            description=message,
            color=discord.Color.green()
        )
        
        # Afficher la description (avec limite)
        description = cmd_data.get("description", "No description set")
        if len(description) > 1000:
            description = description[:997] + "..."
        
        # Afficher la réponse (avec limite)
        response = cmd_data.get("response", "No response set")
        if len(response) > 900:
            response_preview = response[:897] + "..."
            response_value = f"{response_preview}\n*(Response truncated, full length: {len(response)} characters)*"
        else:
            response_value = response
        
        embed.add_field(name="Description", value=description, inline=False)
        embed.add_field(name="Response", value=response_value, inline=False)
        return embed

    @commands.hybrid_command(
        name="edit_command",
        description="Edit an existing custom command with an interactive interface."
    )
    @app_commands.default_permissions(administrator=True)
    @commands.has_permissions(administrator=True)
    async def edit_command(self, ctx):
        """Edit a custom command with a modern UI interface."""
        # Répondre immédiatement pour éviter les erreurs d'interaction
        if ctx.interaction:
            await ctx.defer()
            
        # Récupérer toutes les commandes disponibles pour ce serveur
        server_id = str(ctx.guild.id)
        available_commands = []
        
        # Commandes globales
        for cmd_name in self.commands_data.get("global", {}):
            available_commands.append({"name": cmd_name, "scope": "global"})
        
        # Commandes du serveur
        if server_id in self.commands_data.get("servers", {}):
            for cmd_name in self.commands_data["servers"][server_id]:
                available_commands.append({"name": cmd_name, "scope": "server"})
        
        if not available_commands:
            await ctx.send("No custom commands available to edit. Use `/create_command` to create one!")
            return
        
        # Créer le sélecteur de commandes
        select_options = []
        for cmd in available_commands:
            scope_emoji = "🌐" if cmd["scope"] == "global" else "🔒"
            select_options.append(
                discord.SelectOption(
                    label=cmd["name"], 
                    description=f"{scope_emoji} {cmd['scope'].capitalize()} command",
                    value=f"{cmd['scope']}|{cmd['name']}"
                )
            )
        
        class CommandSelector(discord.ui.Select):
            def __init__(self, cog, ctx):
                self.cog = cog
                self.ctx = ctx
                super().__init__(
                    placeholder="Select a command to edit...",
                    options=select_options,
                    min_values=1,
                    max_values=1
                )
            
            async def callback(self, interaction):
                # Extraire le scope et le nom de la commande
                scope, cmd_name = self.values[0].split("|")
                
                # Récupérer les données de la commande
                if scope == "global":
                    cmd_data = self.cog.commands_data["global"][cmd_name]
                else:
                    cmd_data = self.cog.commands_data["servers"][server_id][cmd_name]
                
                # Créer une vue pour l'édition
                edit_view = CommandEditor(self.cog, self.ctx, scope, cmd_name, cmd_data, server_id)
                
                # Afficher l'embed d'édition
                embed = self.cog.create_command_info_embed(cmd_name, cmd_data, "Select what you want to edit:")
                await interaction.response.edit_message(embed=embed, view=edit_view)
        
        class SelectorView(discord.ui.View):
            def __init__(self, cog, ctx):
                super().__init__(timeout=180)
                self.cog = cog
                self.add_item(CommandSelector(cog, ctx))
        
        # Afficher l'embed initial avec le sélecteur de commandes
        embed = discord.Embed(
            title="🔧 Edit Custom Command",
            description="Select a command to edit from the dropdown menu below:",
            color=discord.Color.blue()
        )
        
        view = SelectorView(self, ctx)
        await ctx.send(embed=embed, view=view)
    
    @commands.command(name="sync_commands", hidden=True)
    @commands.is_owner()
    async def sync_commands(self, ctx):
        """Synchronize slash commands with Discord."""
        await ctx.send("Synchronizing slash commands...")
        try:
            synced = await self.bot.tree.sync()
            await ctx.send(f"✅ Successfully synced {len(synced)} slash commands!")
        except Exception as e:
            await ctx.send(f"❌ Error syncing commands: {e}")

    @commands.Cog.listener()
    async def on_ready(self):
        print(f"CommandBuilder chargé et prêt.")

class ResponseModal(discord.ui.Modal, title="Edit Command Response"):
    response = discord.ui.TextInput(
        label="Response",
        style=discord.TextStyle.paragraph,
        placeholder="Enter the new response for this command...",
        required=True,
        max_length=1000  # Limite Discord
    )
    
    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer()
        
        # Get the new response
        new_response = self.response.value.strip()
        
        # Update the command data
        view = self.view
        if view.scope == "global":
            view.cog.commands_data["global"][view.cmd_name]["response"] = new_response
        else:
            view.cog.commands_data["servers"][view.server_id][view.cmd_name]["response"] = new_response
        
        view.cmd_data["response"] = new_response
        view.cog.save_commands()
        
        # Update the embed
        embed = view.cog.create_command_info_embed(view.cmd_name, view.cmd_data, "Command response updated!")
        
        # Send a follow-up message with the updated info
        await interaction.followup.send(embed=embed, view=view)

class DescriptionModal(discord.ui.Modal, title="Edit Command Description"):
    description = discord.ui.TextInput(
        label="Description",
        style=discord.TextStyle.paragraph,
        placeholder="Enter the new description for this command...",
        required=True,
        max_length=1000
    )
    
    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer()
        
        # Get the new description
        new_description = self.description.value.strip()
        
        # Update the command data
        view = self.view
        if view.scope == "global":
            view.cog.commands_data["global"][view.cmd_name]["description"] = new_description
        else:
            view.cog.commands_data["servers"][view.server_id][view.cmd_name]["description"] = new_description
        
        view.cmd_data["description"] = new_description
        view.cog.save_commands()
        
        # Update the embed
        embed = view.cog.create_command_info_embed(view.cmd_name, view.cmd_data, "Command description updated!")
        
        # Send a follow-up message with the updated info
        await interaction.followup.send(embed=embed, view=view)
        
    async def on_error(self, interaction: discord.Interaction, error: Exception) -> None:
        await interaction.response.send_message(f"An error occurred: {error}", ephemeral=True)

class CommandEditor(discord.ui.View):
    def __init__(self, cog, ctx, scope, cmd_name, cmd_data, server_id):
        super().__init__(timeout=300)
        self.cog = cog
        self.ctx = ctx
        self.scope = scope
        self.cmd_name = cmd_name
        self.cmd_data = cmd_data.copy()
        self.server_id = server_id
    
    @discord.ui.button(label="Edit Response", style=discord.ButtonStyle.primary)
    async def edit_response(self, interaction, button):
        # Vérifier la longueur de la réponse actuelle
        response = self.cmd_data.get("response", "")
        
        if len(response) > 1000:
            # Si la réponse est trop longue pour un modal, proposer une édition alternative
            await interaction.response.send_message(
                f"⚠️ The current response is too long ({len(response)} characters) for Discord's modal limit (1000 characters).\n\n"
                f"Here's a preview of the current response:\n```\n{response[:300]}...\n```\n"
                f"Please send your new response as a message in this channel. Type `cancel` to cancel.",
                ephemeral=True
            )
            
            # Attendre la réponse de l'utilisateur dans le chat
            def check(m):
                return m.author == interaction.user and m.channel == interaction.channel
            
            try:
                msg = await self.cog.bot.wait_for('message', timeout=300.0, check=check)
                
                # Si l'utilisateur veut annuler
                if msg.content.lower() == "cancel":
                    await interaction.followup.send("Editing cancelled.", ephemeral=True)
                    return
                
                # Mettre à jour la réponse
                new_response = msg.content
                
                # Mettre à jour les données
                if self.scope == "global":
                    self.cog.commands_data["global"][self.cmd_name]["response"] = new_response
                else:
                    self.cog.commands_data["servers"][self.server_id][self.cmd_name]["response"] = new_response
                
                self.cmd_data["response"] = new_response
                self.cog.save_commands()
                
                # Confirmer la mise à jour
                embed = self.cog.create_command_info_embed(self.cmd_name, self.cmd_data, "Command response updated!")
                await interaction.followup.send(embed=embed)
                
                # Supprimer le message de l'utilisateur pour éviter l'encombrement
                try:
                    await msg.delete()
                except:
                    pass
                
            except asyncio.TimeoutError:
                await interaction.followup.send("You took too long to respond. Editing cancelled.", ephemeral=True)
        
        else:
            # Si la réponse est dans la limite, utiliser le modal comme avant
            modal = ResponseModal()
            modal.response.default = response
            modal.view = self
            await interaction.response.send_modal(modal)
    
    @discord.ui.button(label="Edit Description", style=discord.ButtonStyle.primary)
    async def edit_description(self, interaction, button):
        modal = DescriptionModal()
        modal.description.default = self.cmd_data.get("description", "")
        modal.view = self
        
        # Send the modal
        await interaction.response.send_modal(modal)
    
    @discord.ui.button(label="Delete Command", style=discord.ButtonStyle.danger)
    async def delete_command(self, interaction, button):
        # Create confirmation view
        confirm_view = ConfirmView(self)
        
        # Send confirmation message
        await interaction.response.send_message(
            f"⚠️ Are you sure you want to delete the command `{self.cmd_name}`?", 
            view=confirm_view, 
            ephemeral=True
        )
    
    @discord.ui.button(label="View Full Response", style=discord.ButtonStyle.secondary)
    async def view_full_response(self, interaction, button):
        response = self.cmd_data.get("response", "")
        
        if len(response) > 1900:
            # Si la réponse est trop longue pour un message Discord
            chunks = [response[i:i+1900] for i in range(0, len(response), 1900)]
            await interaction.response.send_message(f"Full response for `{self.cmd_name}` (part 1/{len(chunks)}):", ephemeral=True)
            
            for i, chunk in enumerate(chunks):
                if i == 0:  # Premier morceau déjà envoyé
                    continue
                await interaction.followup.send(f"Part {i+1}/{len(chunks)}:\n{chunk}", ephemeral=True)
        else:
            await interaction.response.send_message(f"Full response for `{self.cmd_name}`:\n{response}", ephemeral=True)
    
    @discord.ui.button(label="Done", style=discord.ButtonStyle.success)
    async def done(self, interaction, button):
        await interaction.response.edit_message(
            embed=discord.Embed(
                title="✅ Command Edited",
                description=f"The command `{self.cmd_name}` has been successfully updated!",
                color=discord.Color.green()
            ),
            view=None
        )

class ConfirmView(discord.ui.View):
    def __init__(self, editor_view):
        super().__init__(timeout=60)
        self.editor_view = editor_view
    
    @discord.ui.button(label="Yes, Delete", style=discord.ButtonStyle.danger)
    async def confirm(self, interaction, button):
        # Delete the command
        if self.editor_view.scope == "global":
            del self.editor_view.cog.commands_data["global"][self.editor_view.cmd_name]
        else:
            del self.editor_view.cog.commands_data["servers"][self.editor_view.server_id][self.editor_view.cmd_name]
        
        # Save changes
        self.editor_view.cog.save_commands()
        
        # Remove the command from the bot
        if self.editor_view.cog.bot.get_command(self.editor_view.cmd_name):
            self.editor_view.cog.bot.remove_command(self.editor_view.cmd_name)
        
        # Send confirmation
        await interaction.response.edit_message(
            content=f"✅ Command `{self.editor_view.cmd_name}` has been deleted.",
            view=None
        )
        
        # Update the original message
        await self.editor_view.ctx.send(
            embed=discord.Embed(
                title="Command Deleted",
                description=f"Command `{self.editor_view.cmd_name}` has been deleted.",
                color=discord.Color.red()
            )
        )
    
    @discord.ui.button(label="Cancel", style=discord.ButtonStyle.secondary)
    async def cancel(self, interaction, button):
        await interaction.response.edit_message(
            content="Command deletion cancelled.",
            view=None
        )

async def setup(bot):
    await bot.add_cog(CommandBuilder(bot))