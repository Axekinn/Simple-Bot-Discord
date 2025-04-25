import discord
from discord.ext import commands
from discord.ui import View, Button, Select
from discord import app_commands
import json
import os
import asyncio
from typing import Literal

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
        # Répondre immédiatement avec defer()
        await ctx.defer(ephemeral=True)
        
        # Utiliser des modaux pour une meilleure expérience utilisateur
        class CommandCreationModal(discord.ui.Modal, title="Create Custom Command"):
            command_name = discord.ui.TextInput(
                label="Command Name",
                placeholder="Enter a name for your command (no spaces)",
                required=True,
                max_length=32
            )
            
            command_description = discord.ui.TextInput(
                label="Description",
                placeholder="Enter a description for this command",
                required=True,
                max_length=100
            )
            
            command_response = discord.ui.TextInput(
                label="Response",
                style=discord.TextStyle.paragraph,
                placeholder="What should the bot say when this command is used?",
                required=True,
                max_length=1000
            )
            
            is_global = discord.ui.TextInput(
                label="Global Command?",
                placeholder="Type 'yes' for global, 'no' for server only",
                required=True,
                max_length=3
            )
            
            async def on_submit(self, interaction: discord.Interaction):
                await interaction.response.defer(ephemeral=True)  # Ajouter ephemeral=True ici
                
                command_name = self.command_name.value.strip().lower()
                description = self.command_description.value.strip()
                response = self.command_response.value.strip()
                is_global = self.is_global.value.lower() in ['yes', 'y', 'true']
                
                # Valider le nom de la commande
                if not command_name.isalnum():
                    await interaction.followup.send("Command name must be alphanumeric without spaces.", ephemeral=True)
                    return
                
                # Vérifier si la commande existe déjà
                server_id = str(interaction.guild.id)
                cog = self.view.cog
                
                if is_global and command_name in cog.commands_data.get("global", {}):
                    await interaction.followup.send(f"A global command named `{command_name}` already exists.", ephemeral=True)
                    return
                
                if not is_global and server_id in cog.commands_data.get("servers", {}) and command_name in cog.commands_data["servers"][server_id]:
                    await interaction.followup.send(f"A server command named `{command_name}` already exists on this server.", ephemeral=True)
                    return
                
                # Vérifier si la réponse est proche de la limite pour proposer l'ajout de texte
                is_near_limit = len(response) >= 900  # Si proche de la limite de 1000
                
                # Ajouter la commande
                command_data = {
                    "description": description,
                    "response": response
                }
                
                if is_global:
                    if "global" not in cog.commands_data:
                        cog.commands_data["global"] = {}
                    cog.commands_data["global"][command_name] = command_data
                else:
                    if "servers" not in cog.commands_data:
                        cog.commands_data["servers"] = {}
                    if server_id not in cog.commands_data["servers"]:
                        cog.commands_data["servers"][server_id] = {}
                    cog.commands_data["servers"][server_id][command_name] = command_data
                
                # Sauvegarder et enregistrer la commande
                cog.save_commands()
                cog.register_command(command_name, command_data, is_global, server_id if not is_global else None)
                
                # Confirmer la création avec option d'extension si la réponse est proche de la limite
                scope_text = "global" if is_global else f"server-specific to {interaction.guild.name}"
                
                if is_near_limit:
                    # Créer une vue avec bouton pour ajouter du texte
                    continue_view = ContinueResponseView(cog, command_name, is_global, server_id)
                    
                    embed = discord.Embed(
                        title="✅ Command Created",
                        description=f"The command `{command_name}` has been created and is {scope_text}!\n\n⚠️ Your response is near the character limit. Would you like to add more text?",
                        color=discord.Color.gold()
                    )
                    await interaction.followup.send(embed=embed, view=continue_view, ephemeral=True)  # Ajouter ephemeral=True
                else:
                    embed = discord.Embed(
                        title="✅ Command Created",
                        description=f"The command `{command_name}` has been created and is {scope_text}!",
                        color=discord.Color.green()
                    )
                    await interaction.followup.send(embed=embed, ephemeral=True)  # Ajouter ephemeral=True
                
            @discord.ui.button(label="Add More Text", style=discord.ButtonStyle.primary)
            async def add_text(self, interaction, button):
                # Au lieu d'attendre des messages dans le chat, utiliser un modal
                class AdditionalTextModal(discord.ui.Modal, title="Add More Text"):
                    additional_text = discord.ui.TextInput(
                        label="Additional Text",
                        style=discord.TextStyle.paragraph,
                        placeholder="Enter additional text to append...",
                        required=True,
                        max_length=1000
                    )
                    
                    async def on_submit(self, interaction: discord.Interaction):
                        await interaction.response.defer(ephemeral=True)
                        
                        # Obtenir la réponse actuelle
                        if self.view.is_global:
                            current_response = self.view.cog.commands_data["global"][self.view.command_name]["response"]
                            # Ajouter le texte
                            self.view.cog.commands_data["global"][self.view.command_name]["response"] = current_response + "\n" + self.additional_text.value
                            # Obtenir la nouvelle longueur
                            new_length = len(self.view.cog.commands_data["global"][self.view.command_name]["response"])
                        else:
                            current_response = self.view.cog.commands_data["servers"][self.view.server_id][self.view.command_name]["response"]
                            # Ajouter le texte
                            self.view.cog.commands_data["servers"][self.view.server_id][self.view.command_name]["response"] = current_response + "\n" + self.additional_text.value
                            # Obtenir la nouvelle longueur
                            new_length = len(self.view.cog.commands_data["servers"][self.view.server_id][self.view.command_name]["response"])
                        
                        # Sauvegarder les modifications
                        self.view.cog.save_commands()
                        
                        # Créer une vue pour continuer ou terminer
                        continue_view = ContinueOrFinishView(self.view.cog, self.view.command_name, self.view.is_global, self.view.server_id)
                        
                        # Informer l'utilisateur
                        await interaction.followup.send(
                            f"✅ Text added! Current response length: {new_length} characters.\nWould you like to add more text or finish?",
                            view=continue_view,
                            ephemeral=True
                        )
                
                # Créer et envoyer le modal
                modal = AdditionalTextModal()
                modal.view = self
                await interaction.response.send_modal(modal)
            
            @discord.ui.button(label="Add More Text", style=discord.ButtonStyle.primary)
            async def add_more(self, interaction, button):
                # Réutiliser la même logique que pour ajouter du texte
                continue_view = ContinueResponseView(self.cog, self.command_name, self.is_global, self.server_id)
                await continue_view.add_text(interaction, button)
            
            @discord.ui.button(label="Finish", style=discord.ButtonStyle.success)
            async def finish(self, interaction, button):
                await interaction.response.edit_message(
                    content=f"✅ Command `{self.command_name}` has been successfully updated!",
                    embed=None,
                    view=None
                )

        # Créer une vue simple pour afficher le modal
        class CommandCreationButton(discord.ui.View):
            def __init__(self, cog):
                super().__init__()
                self.cog = cog
                
            @discord.ui.button(label="Create Command", style=discord.ButtonStyle.primary)
            async def create_button(self, interaction, button):
                modal = CommandCreationModal()
                modal.view = self
                await interaction.response.send_modal(modal)
    
        # Envoyer un message initial avec le bouton
        view = CommandCreationButton(self)
        # Utilisez ctx.followup.send au lieu de ctx.send pour les commandes hybrides
        await ctx.followup.send(
            embed=discord.Embed(
                title="🛠️ Create a Custom Command",
                description="Click the button below to create a new command!",
                color=discord.Color.blue()
            ),
            view=view,
            ephemeral=True
        )

    @app_commands.command(
        name="commands",
        description="Browse all available custom commands with an interactive interface."
    )
    @app_commands.describe(
        scope="Show global commands, server commands, or both",
        filter="Filter commands by name or description",
        sort="How to sort the commands list"
    )
    async def slash_list_commands(
        self, 
        interaction: discord.Interaction, 
        scope: Literal["global", "server", "all"] = "all",
        filter: str = None,
        sort: Literal["name", "recent", "usage"] = "name"
    ):
        """Browse all available custom commands with a modern interactive interface."""
        await interaction.response.defer(ephemeral=True)
        
        # Rechargement forcé des commandes depuis le fichier JSON
        self.commands_data = self.load_commands()
        print(f"[COMMANDS] Reloaded commands.json, found {len(self.commands_data.get('global', {}))} global commands")
        
        server_id = str(interaction.guild.id)
        server_cmds_count = len(self.commands_data.get("servers", {}).get(server_id, {}))
        print(f"[COMMANDS] Found {server_cmds_count} commands for server {server_id}")
        
        # Récupérer les commandes selon le scope choisi
        commands_to_show = {}
        
        if scope in ["global", "all"]:
            global_commands = self.commands_data.get("global", {})
            if global_commands:
                commands_to_show["🌐 Global Commands"] = global_commands
                print(f"[COMMANDS] Added {len(global_commands)} global commands to display")
        
        if scope in ["server", "all"]:
            server_commands = self.commands_data.get("servers", {}).get(server_id, {})
            if server_commands:
                commands_to_show[f"🔒 {interaction.guild.name} Commands"] = server_commands
                print(f"[COMMANDS] Added {len(server_commands)} server commands to display")
        
        if not commands_to_show:
            await interaction.followup.send("No custom commands available. Use `/create_command` to create one!", ephemeral=True)
            return
        
        # Filtrer les commandes si un filtre est spécifié
        if filter:
            filter = filter.lower()
            filtered_commands = {}
            
            for category, cmds in commands_to_show.items():
                matching_cmds = {}
                for cmd_name, cmd_data in cmds.items():
                    # Recherche améliorée dans le nom, la description et la réponse
                    cmd_response = cmd_data.get('response', '') if isinstance(cmd_data, dict) else str(cmd_data)
                    if (filter in cmd_name.lower() or 
                        (isinstance(cmd_data, dict) and filter in cmd_data.get('description', '').lower()) or
                        filter in cmd_response.lower()):
                        matching_cmds[cmd_name] = cmd_data
                
                if matching_cmds:
                    filtered_commands[category] = matching_cmds
            
            if not filtered_commands:
                await interaction.followup.send(f"No commands found matching '{filter}'.", ephemeral=True)
                return
            
            commands_to_show = filtered_commands
            
        # Créer le navigateur de commandes amélioré
        command_browser = EnhancedCommandBrowser(self, interaction, commands_to_show, sort_method=sort)
        await command_browser.start()

    @commands.command(name="list_commands", aliases=["commands", "cmds"], hidden=True)
    async def old_list_commands(self, ctx):
        """Redirect to the new slash command version."""
        embed = discord.Embed(
            title="Command Updated",
            description="This command has been updated to a slash command!\n\nPlease use `/commands` instead for an enhanced experience.",
            color=discord.Color.blue()
        )
        embed.set_footer(text="Slash commands provide a better interface and more features")
        await ctx.send(embed=embed, ephemeral=True if ctx.interaction else False)

    @commands.command(name="reload_commands", hidden=True)
    @commands.has_permissions(administrator=True)
    async def reload_commands(self, ctx):
        """Reload commands from the commands.json file."""
        try:
            old_count = sum(len(cmds) for cmds in self.commands_data.values() if isinstance(cmds, dict))
            self.commands_data = self.load_commands()
            self.fix_commands_format()
            self.register_all_commands()
            new_count = sum(len(cmds) for cmds in self.commands_data.values() if isinstance(cmds, dict))
            
            await ctx.send(f"✅ Commands reloaded successfully! ({old_count} → {new_count} commands)", ephemeral=True)
        except Exception as e:
            await ctx.send(f"❌ Error reloading commands: {e}", ephemeral=True)

    @app_commands.command(
        name="edit_command",
        description="Edit an existing custom command"
    )
    @app_commands.default_permissions(administrator=True)
    async def edit_command(self, interaction: discord.Interaction):
        """Edit an existing custom command with an interactive interface."""
        # Répondre immédiatement pour éviter l'erreur unknown integration
        await interaction.response.defer(ephemeral=True)
        
        # Charger les commandes existantes
        server_id = str(interaction.guild.id)
        global_commands = self.commands_data.get("global", {})
        server_commands = self.commands_data.get("servers", {}).get(server_id, {})
        
        if not global_commands and not server_commands:
            await interaction.followup.send("No commands found to edit. Create one with `/create_command` first!", ephemeral=True)
            return
        
        # Créer une vue pour sélectionner la commande à éditer
        class CommandSelectView(discord.ui.View):
            def __init__(self, cog):
                super().__init__(timeout=180)
                self.cog = cog
                
                # Ajouter sélecteur pour commandes globales
                if global_commands:
                    global_select = discord.ui.Select(
                        placeholder="Select a global command to edit",
                        options=[
                            discord.SelectOption(
                                label=f"!{cmd_name}", 
                                value=f"global:{cmd_name}",
                                description=cmd_data.get('description', 'No description')[:100] if isinstance(cmd_data, dict) else 'No description'
                            )
                            for cmd_name, cmd_data in global_commands.items()
                        ][:25],  # Maximum 25 options
                        row=0
                    )
                    global_select.callback = self.command_selected
                    self.add_item(global_select)
                
                # Ajouter sélecteur pour commandes du serveur
                if server_commands:
                    server_select = discord.ui.Select(
                        placeholder="Select a server command to edit",
                        options=[
                            discord.SelectOption(
                                label=f"!{cmd_name}", 
                                value=f"server:{cmd_name}",
                                description=cmd_data.get('description', 'No description')[:100] if isinstance(cmd_data, dict) else 'No description'
                            )
                            for cmd_name, cmd_data in server_commands.items()
                        ][:25],  # Maximum 25 options
                        row=1
                    )
                    server_select.callback = self.command_selected
                    self.add_item(server_select)
            
            async def command_selected(self, interaction: discord.Interaction):
                scope, cmd_name = interaction.data['values'][0].split(':', 1)
                
                # Récupérer les données de la commande
                if scope == "global":
                    cmd_data = self.cog.commands_data["global"][cmd_name]
                else:
                    server_id = str(interaction.guild.id)
                    cmd_data = self.cog.commands_data["servers"][server_id][cmd_name]
                
                # Créer et envoyer le modal d'édition
                await interaction.response.send_modal(
                    CommandEditModal(self.cog, cmd_name, cmd_data, scope == "global")
                )
        
        # Modal pour éditer la commande
        class CommandEditModal(discord.ui.Modal):
            def __init__(self, cog, command_name, command_data, is_global):
                super().__init__(title=f"Edit Command: !{command_name}")
                self.cog = cog
                self.command_name = command_name
                self.is_global = is_global
                self.full_response = None
                
                # Préparer les données de la commande
                description = command_data.get('description', '') if isinstance(command_data, dict) else ''
                response = command_data.get('response', '') if isinstance(command_data, dict) else str(command_data)
                
                # Stocker la réponse complète si elle dépasse la limite
                if len(response) > 1000:
                    self.full_response = response
                    truncated_note = "\n\n[... Response truncated due to length. The full content will be preserved when you save.]"
                    displayable_response = response[:900] + truncated_note
                else:
                    displayable_response = response
                
                # Ajouter les champs au modal
                self.description = discord.ui.TextInput(
                    label="Description",
                    placeholder="Enter a description for this command",
                    default=description,
                    required=True,
                    max_length=100
                )
                self.add_item(self.description)
                
                self.response = discord.ui.TextInput(
                    label="Response",
                    style=discord.TextStyle.paragraph,
                    placeholder="What should the bot say when this command is used?",
                    default=displayable_response,
                    required=True,
                    max_length=1000
                )
                self.add_item(self.response)
                
                if len(response) > 1000:
                    self.edit_note = discord.ui.TextInput(
                        label="Note about long responses",
                        style=discord.TextStyle.paragraph,
                        default="⚠️ This response exceeds 1000 characters. You can edit what you see, but if you want to significantly change the full text, consider creating a new command.",
                        required=False,
                        max_length=300
                    )
                    self.edit_note.disabled = True
                    self.add_item(self.edit_note)
            
            async def on_submit(self, interaction: discord.Interaction):
                await interaction.response.defer(ephemeral=True)
                
                # Déterminer la réponse finale
                response_text = self.response.value.strip()
                
                # Si nous avions une réponse complète stockée et que l'utilisateur n'a pas fait
                # de modifications majeures (moins de 100 caractères de différence avec le texte tronqué),
                # utiliser la réponse complète d'origine
                if self.full_response and ("[... Response truncated due to length" in response_text):
                    response_text = self.full_response
                    
                # Mettre à jour les données de la commande
                command_data = {
                    "description": self.description.value.strip(),
                    "response": response_text
                }
                
                # Vérifier si la réponse est proche de la limite
                is_near_limit = len(response_text) >= 900  # Si proche de la limite de 1000
                
                if self.is_global:
                    self.cog.commands_data["global"][self.command_name] = command_data
                else:
                    server_id = str(interaction.guild.id)
                    self.cog.commands_data["servers"][server_id][self.command_name] = command_data
                
                # Sauvegarder les modifications
                self.cog.save_commands()
                
                # Confirmer l'édition avec option d'extension si la réponse est proche de la limite
                if is_near_limit:
                    # Créer une vue avec bouton pour ajouter du texte
                    continue_view = ContinueResponseView(self.cog, self.command_name, self.is_global, 
                                                       server_id if not self.is_global else None)
                    
                    embed = discord.Embed(
                        title="✅ Command Updated",
                        description=f"The command `{self.command_name}` has been updated!\n\n⚠️ Your response is near the character limit. Would you like to add more text?",
                        color=discord.Color.gold()
                    )
                    await interaction.followup.send(embed=embed, view=continue_view, ephemeral=True)
                else:
                    embed = discord.Embed(
                        title="✅ Command Updated",
                        description=f"The command `{self.command_name}` has been updated successfully!" + 
                                    (f"\n\n📝 Response length: {len(response_text)} characters" if len(response_text) > 500 else ""),
                        color=discord.Color.green()
                    )
                    await interaction.followup.send(embed=embed, ephemeral=True)

        # Afficher la vue de sélection
        await interaction.followup.send(
            embed=discord.Embed(
                title="🖊️ Edit a Custom Command",
                description="Select the command you want to edit from the dropdown menus below:",
                color=discord.Color.blue()
            ),
            view=CommandSelectView(self),
            ephemeral=True
        )

# Modal pour la recherche de commandes
class EnhancedSearchModal(discord.ui.Modal, title="Search Commands"):
    search_query = discord.ui.TextInput(
        label="Search",
        placeholder="Enter command name, description or response content",
        required=True,
        max_length=100
    )
    
    def __init__(self, browser):
        super().__init__()
        self.browser = browser
    
    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        
        query = self.search_query.value.lower()
        
        # Filter commands in all categories
        filtered_commands = {}
        
        for category, cmds in self.browser.commands_data.items():
            matching_cmds = {}
            for cmd_name, cmd_data in cmds.items():
                # Search in name, description and response
                cmd_response = cmd_data.get('response', '') if isinstance(cmd_data, dict) else str(cmd_data)
                if (query in cmd_name.lower() or 
                    (isinstance(cmd_data, dict) and query in cmd_data.get('description', '').lower()) or
                    query in cmd_response.lower()):
                    matching_cmds[cmd_name] = cmd_data
            
            if matching_cmds:
                filtered_commands[category] = matching_cmds
        
        if not filtered_commands:
            await interaction.followup.send(f"No commands found matching '{query}'.", ephemeral=True)
            return
        
        # Update browser with filtered results
        self.browser.commands_data = filtered_commands
        self.browser.categories = list(filtered_commands.keys())
        self.browser.current_category = 0
        self.browser.current_page = 0
        
        # Update the view and embed
        embed = self.browser.create_commands_embed()
        self.browser.view = self.browser.create_navigation_view()
        
        # Include search indication in embed
        embed.set_footer(text=f"Search results for: {query} | Use Refresh to clear")
        
        await interaction.edit_original_response(embed=embed, view=self.browser.view)

# Classe améliorée pour la gestion des commandes
class EnhancedCommandBrowser:
    def __init__(self, cog, interaction, commands_categories, sort_method="name"):
        self.cog = cog
        self.interaction = interaction
        self.categories = list(commands_categories.keys())
        self.commands_data = commands_categories
        self.current_category = 0
        self.current_page = 0
        self.commands_per_page = 5  # Réduit pour plus de lisibilité et d'espace pour les détails
        self.selected_command = None
        self.view = None
        self.sort_method = sort_method
        self.message = None
        self.detailed_view = False
    
    async def start(self):
        """Démarre l'affichage du navigateur de commandes"""
        self.view = self.create_navigation_view()
        embed = self.create_commands_embed()
        self.message = await self.interaction.followup.send(embed=embed, view=self.view, ephemeral=True)
    
    def create_navigation_view(self):
        """Crée la vue avec les boutons de navigation améliorée"""
        view = discord.ui.View(timeout=600)  # Plus long timeout
        
        # Première ligne: Navigation de page
        prev_button = discord.ui.Button(
            style=discord.ButtonStyle.secondary,
            emoji="◀️",
            disabled=self.current_page == 0,
            row=0
        )
        prev_button.callback = self.previous_page
        view.add_item(prev_button)
        
        page_indicator = discord.ui.Button(
            style=discord.ButtonStyle.secondary,
            label=f"Page {self.current_page + 1}/{max(1, self.get_max_pages())}",
            disabled=True,
            row=0
        )
        view.add_item(page_indicator)
        
        next_button = discord.ui.Button(
            style=discord.ButtonStyle.secondary,
            emoji="▶️",
            disabled=self.current_page >= self.get_max_pages() - 1,
            row=0
        )
        next_button.callback = self.next_page
        view.add_item(next_button)
        
        # Deuxième ligne: Actions principales
        # Vue détaillée / Vue liste
        view_toggle = discord.ui.Button(
            style=discord.ButtonStyle.primary,
            emoji="🔍" if not self.detailed_view else "📋",
            label="Detailed View" if not self.detailed_view else "List View",
            row=1
        )
        view_toggle.callback = self.toggle_view_mode
        view.add_item(view_toggle)
        
        # Ajouter une nouvelle commande
        add_button = discord.ui.Button(
            style=discord.ButtonStyle.success,
            emoji="➕",
            label="Create Command",
            row=1
        )
        add_button.callback = self.create_command
        view.add_item(add_button)
        
        # Recherche
        search_button = discord.ui.Button(
            style=discord.ButtonStyle.primary,
            emoji="🔎",
            label="Search",
            row=1
        )
        search_button.callback = self.search_commands
        view.add_item(search_button)
        
        # Troisième ligne: Menu déroulant pour le tri
        sort_select = discord.ui.Select(
            placeholder="Sort by...",
            options=[
                discord.SelectOption(label="Sort by Name", value="name", emoji="🔤", default=self.sort_method=="name"),
                discord.SelectOption(label="Sort by Recent", value="recent", emoji="🕒", default=self.sort_method=="recent"),
                discord.SelectOption(label="Sort by Usage", value="usage", emoji="📊", default=self.sort_method=="usage")
            ],
            row=2
        )
        sort_select.callback = self.change_sort
        view.add_item(sort_select)
        
        # Quatrième ligne: Menu déroulant pour changer de catégorie
        if len(self.categories) > 1:
            category_select = discord.ui.Select(
                placeholder="Select category",
                options=[
                    discord.SelectOption(
                        label=cat.replace("🌐 ", "").replace("🔒 ", "")[:25],
                        value=str(i),
                        emoji="🌐" if "Global" in cat else "🔒",
                        description=f"{len(self.commands_data[cat])} commands",
                        default=i == self.current_category
                    )
                    for i, cat in enumerate(self.categories)
                ],
                row=3  # Moved to row 3 to prevent overflow
            )
            category_select.callback = self.change_category
            view.add_item(category_select)
        
        # Cinquième ligne: Actions utilitaires
        # Exporter la liste
        export_button = discord.ui.Button(
            style=discord.ButtonStyle.secondary,
            emoji="📤",
            label="Export",
            row=4
        )
        export_button.callback = self.export_commands
        view.add_item(export_button)
        
        # Rafraîchir
        refresh_button = discord.ui.Button(
            style=discord.ButtonStyle.secondary,
            emoji="🔄",
            label="Refresh",
            row=4
        )
        refresh_button.callback = self.refresh_list
        view.add_item(refresh_button)
        
        return view
    
    async def previous_page(self, interaction):
        """Naviguer vers la page précédente"""
        await interaction.response.defer()
        if self.current_page > 0:
            self.current_page -= 1
            embed = self.create_commands_embed()
            self.view = self.create_navigation_view()
            await interaction.edit_original_response(embed=embed, view=self.view)
    
    async def next_page(self, interaction):
        """Naviguer vers la page suivante"""
        await interaction.response.defer()
        if self.current_page < self.get_max_pages() - 1:
            self.current_page += 1
            embed = self.create_commands_embed()
            self.view = self.create_navigation_view()
            await interaction.edit_original_response(embed=embed, view=self.view)
    
    async def toggle_view_mode(self, interaction):
        """Basculer entre vue détaillée et vue liste"""
        await interaction.response.defer()
        self.detailed_view = not self.detailed_view
        self.current_page = 0  # Revenir à la première page lors du changement de vue
        embed = self.create_commands_embed()
        self.view = self.create_navigation_view()
        await interaction.edit_original_response(embed=embed, view=self.view)
    
    async def change_category(self, interaction):
        """Changer de catégorie de commandes"""
        await interaction.response.defer()
        self.current_category = int(interaction.data["values"][0])
        self.current_page = 0
        embed = self.create_commands_embed()
        self.view = self.create_navigation_view()
        await interaction.edit_original_response(embed=embed, view=self.view)
    
    async def change_sort(self, interaction):
        """Changer la méthode de tri"""
        await interaction.response.defer()
        self.sort_method = interaction.data["values"][0]
        self.current_page = 0
        embed = self.create_commands_embed()
        self.view = self.create_navigation_view()
        await interaction.edit_original_response(embed=embed, view=self.view)
    
    async def search_commands(self, interaction):
        """Ouvrir un modal de recherche amélioré"""
        modal = EnhancedSearchModal(self)
        await interaction.response.send_modal(modal)
    
    async def create_command(self, interaction):
        """Rediriger vers la création de commande"""
        await interaction.response.defer(ephemeral=True)
        await interaction.followup.send(
            "Use the `/create_command` command to create a new custom command!", 
            ephemeral=True
        )
    
    async def export_commands(self, interaction):
        """Exporter les commandes dans un fichier amélioré"""
        await interaction.response.defer()
        category = self.categories[self.current_category]
        commands = self.commands_data[category]
        
        # Créer un contenu formaté pour l'export
        content = f"# {category}\n\n"
        content += f"> Exported on {discord.utils.utcnow().strftime('%Y-%m-%d at %H:%M UTC')}\n"
        content += f"> Server: {self.interaction.guild.name}\n\n"
        
        for cmd_name, cmd_data in sorted(commands.items()):
            description = cmd_data.get('description', 'No description') if isinstance(cmd_data, dict) else 'No description'
            content += f"## !{cmd_name}\n"
            content += f"Description: {description}\n\n"
            
            if isinstance(cmd_data, dict) and 'response' in cmd_data:
                content += f"Response:\n```\n{cmd_data['response']}\n```\n\n"

        # Créer un fichier temporaire
        timestamp = discord.utils.utcnow().strftime('%Y%m%d_%H%M%S')
        filename = f"commands_{category.replace(' ', '_').replace(':', '')}_{timestamp}.md"
        with open(filename, "w", encoding="utf-8") as f:
            f.write(content)
        
        # Envoyer le fichier
        file = discord.File(filename)
        await interaction.followup.send(
            "📤 Here's your exported commands list:",
            file=file,
            ephemeral=True
        )
        
        # Supprimer le fichier temporaire
        try:
            os.remove(filename)
        except:
            pass
    
    async def refresh_list(self, interaction):
        """Rafraîchir la liste des commandes"""
        await interaction.response.defer()
        # Recharger les données des commandes
        self.cog.commands_data = self.cog.load_commands()
        
        server_id = str(self.interaction.guild.id)
        commands_to_show = {}
        
        # Déterminer le scope actuel en fonction de la catégorie courante
        current_scope = "global" if "Global" in self.categories[self.current_category] else "server"
        
        if current_scope == "global" or current_scope == "all":
            global_commands = self.cog.commands_data.get("global", {})
            if global_commands:
                commands_to_show["🌐 Global Commands"] = global_commands
        
        if current_scope == "server" or current_scope == "all":
            server_commands = self.cog.commands_data.get("servers", {}).get(server_id, {})
            if server_commands:
                commands_to_show[f"🔒 {self.interaction.guild.name} Commands"] = server_commands
        
        # Mettre à jour les données
        self.commands_data = commands_to_show
        self.categories = list(commands_to_show.keys())
        self.current_category = min(self.current_category, max(0, len(self.categories) - 1))
        self.current_page = min(self.current_page, max(0, self.get_max_pages() - 1))
        
        # Mettre à jour l'affichage
        embed = self.create_commands_embed()
        self.view = self.create_navigation_view()
        await interaction.edit_original_response(
            content="✅ Commands list refreshed!",
            embed=embed, 
            view=self.view
        )
    
    def create_commands_embed(self):
        """Créer un embed pour afficher les commandes"""
        category = self.categories[self.current_category]
        commands = self.commands_data[category]
        
        embed = discord.Embed(
            title=f"{category} Commands",
            description=f"Showing commands for {category}.",
            color=discord.Color.blue()
        )
        
        # Trier les commandes
        sorted_commands = sorted(commands.items(), key=lambda x: x[0])  # Tri par nom par défaut
        
        # Afficher les commandes par page
        start_index = self.current_page * self.commands_per_page
        end_index = start_index + self.commands_per_page
        commands_to_display = sorted_commands[start_index:end_index]
        
        for cmd_name, cmd_data in commands_to_display:
            description = cmd_data.get('description', 'No description') if isinstance(cmd_data, dict) else 'No description'
            response = cmd_data.get('response', 'No response') if isinstance(cmd_data, dict) else str(cmd_data)
            embed.add_field(name=f"!{cmd_name}", value=f"**Description:** {description}\n**Response:** {response[:200]}...", inline=False)
        
        embed.set_footer(text=f"Page {self.current_page + 1}/{max(1, self.get_max_pages())}")
        return embed
    
    def get_max_pages(self):
        """Obtenir le nombre maximum de pages"""
        category = self.categories[self.current_category]
        commands = self.commands_data[category]
        return (len(commands) + self.commands_per_page - 1) // self.commands_per_page

# Ajouter ces classes en-dessous de la définition de la classe CommandBuilder
# mais avant EnhancedSearchModal

# Vue pour continuer à ajouter du texte à la réponse
class ContinueResponseView(discord.ui.View):
    def __init__(self, cog, command_name, is_global, server_id):
        super().__init__(timeout=300)
        self.cog = cog
        self.command_name = command_name
        self.is_global = is_global
        self.server_id = server_id
        
    @discord.ui.button(label="Add More Text", style=discord.ButtonStyle.primary)
    async def add_text(self, interaction, button):
        # Au lieu d'attendre des messages dans le chat, utiliser un modal
        class AdditionalTextModal(discord.ui.Modal, title="Add More Text"):
            additional_text = discord.ui.TextInput(
                label="Additional Text",
                style=discord.TextStyle.paragraph,
                placeholder="Enter additional text to append...",
                required=True,
                max_length=1000
            )
            
            async def on_submit(self, interaction: discord.Interaction):
                await interaction.response.defer(ephemeral=True)
                
                # Obtenir la réponse actuelle
                if self.view.is_global:
                    current_response = self.view.cog.commands_data["global"][self.view.command_name]["response"]
                    # Ajouter le texte
                    self.view.cog.commands_data["global"][self.view.command_name]["response"] = current_response + "\n" + self.additional_text.value
                    # Obtenir la nouvelle longueur
                    new_length = len(self.view.cog.commands_data["global"][self.view.command_name]["response"])
                else:
                    current_response = self.view.cog.commands_data["servers"][self.view.server_id][self.view.command_name]["response"]
                    # Ajouter le texte
                    self.view.cog.commands_data["servers"][self.view.server_id][self.view.command_name]["response"] = current_response + "\n" + self.additional_text.value
                    # Obtenir la nouvelle longueur
                    new_length = len(self.view.cog.commands_data["servers"][self.view.server_id][self.view.command_name]["response"])
                
                # Sauvegarder les modifications
                self.view.cog.save_commands()
                
                # Créer une vue pour continuer ou terminer
                continue_view = ContinueOrFinishView(self.view.cog, self.view.command_name, self.view.is_global, self.view.server_id)
                
                # Informer l'utilisateur
                await interaction.followup.send(
                    f"✅ Text added! Current response length: {new_length} characters.\nWould you like to add more text or finish?",
                    view=continue_view,
                    ephemeral=True
                )
        
        # Créer et envoyer le modal
        modal = AdditionalTextModal()
        modal.view = self
        await interaction.response.send_modal(modal)

# Nouvelle vue pour continuer ou terminer
class ContinueOrFinishView(discord.ui.View):
    def __init__(self, cog, command_name, is_global, server_id):
        super().__init__(timeout=300)
        self.cog = cog
        self.command_name = command_name
        self.is_global = is_global
        self.server_id = server_id
    
    @discord.ui.button(label="Add More Text", style=discord.ButtonStyle.primary)
    async def add_more(self, interaction, button):
        # Réutiliser la même logique que pour ajouter du texte
        continue_view = ContinueResponseView(self.cog, self.command_name, self.is_global, self.server_id)
        await continue_view.add_text(interaction, button)
    
    @discord.ui.button(label="Finish", style=discord.ButtonStyle.success)
    async def finish(self, interaction, button):
        await interaction.response.edit_message(
            content=f"✅ Command `{self.command_name}` has been successfully updated!",
            embed=None,
            view=None
        )

async def setup(bot):
    await bot.add_cog(CommandBuilder(bot))

