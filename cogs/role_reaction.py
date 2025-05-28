import discord
from discord.ext import commands
from discord import app_commands
from typing import Dict, List, Optional


class RoleEmojiPair:
    """Classe pour stocker une paire rôle/emoji"""
    def __init__(self, role: discord.Role, emoji_str: str, emoji_display: str):
        self.role = role
        self.emoji_str = emoji_str
        self.emoji_display = emoji_display

class RoleSetupModal(discord.ui.Modal, title='Configuration des rôles'):
    def __init__(self):
        super().__init__()
        self.title_input = discord.ui.TextInput(
            label='Titre du message',
            placeholder='Choisissez vos rôles',
            default='Assignation de rôles',
            required=True,
            max_length=256
        )
        self.description_input = discord.ui.TextInput(
            label='Description (optionnelle)',
            placeholder='Cliquez sur les réactions pour obtenir des rôles',
            required=False,
            style=discord.TextStyle.paragraph,
            max_length=4000
        )
        self.add_item(self.title_input)
        self.add_item(self.description_input)

    async def on_submit(self, interaction: discord.Interaction):
        # Créer la vue de configuration des rôles
        view = RoleSetupView(interaction.user, self.title_input.value, self.description_input.value)
        # Transmettre la référence au cog
        view.cog = interaction.client.get_cog('RoleReaction')
        await interaction.response.send_message(
            "Ajoutez des paires rôle/emoji à votre message :", 
            view=view, 
            ephemeral=True
        )

class RoleEmojiSelectionView(discord.ui.View):
    def __init__(self, parent_view):
        super().__init__(timeout=300)
        self.parent_view = parent_view
        self.selected_role = None
        self.selected_emoji = None
        
        # Ajouter un sélecteur de rôle
        self.role_select = discord.ui.RoleSelect(
            placeholder="Choisissez un rôle...",
            min_values=1,
            max_values=1,
            row=0
        )
        self.role_select.callback = self.role_selected
        self.add_item(self.role_select)
        
        # Ajouter les émojis communs sur plusieurs lignes
        self.common_emojis = [
            # Ligne 1 - Expressions
            ["😀", "😂", "😍", "🥰", "😎"],
            # Ligne 2 - Symboles
            ["✅", "❌", "⭐", "🔥", "💯"],
            # Ligne 3 - Objets
            ["🎮", "🎵", "📱", "💻", "🎬"]
        ]
        
        # Créer les boutons d'émojis
        for row_idx, emoji_row in enumerate(self.common_emojis, 1):
            for emoji in emoji_row:
                button = discord.ui.Button(
                    label="", 
                    emoji=emoji, 
                    style=discord.ButtonStyle.secondary,
                    row=row_idx
                )
                button.callback = self.create_emoji_callback(emoji)
                self.add_item(button)
        
        # Bouton pour les emojis personnalisés
        self.custom_emoji_button = discord.ui.Button(
            label="Emoji personnalisé...",
            style=discord.ButtonStyle.primary,
            row=4
        )
        self.custom_emoji_button.callback = self.custom_emoji_clicked
        self.add_item(self.custom_emoji_button)
        
        # Bouton d'annulation
        self.cancel_button = discord.ui.Button(
            label="Annuler",
            style=discord.ButtonStyle.danger,
            row=4
        )
        self.cancel_button.callback = self.cancel_clicked
        self.add_item(self.cancel_button)
    
    def create_emoji_callback(self, emoji):
        async def emoji_callback(interaction):
            self.selected_emoji = emoji
            await self.validate_selection(interaction)
        return emoji_callback
    
    async def role_selected(self, interaction):
        self.selected_role = self.role_select.values[0]
        await interaction.response.defer()
    
    async def custom_emoji_clicked(self, interaction):
        # Créer une vue pour afficher les émojis du serveur
        view = ServerEmojiSelectionView(self)
        await interaction.response.send_message(
            "Sélectionnez un emoji du serveur :",
            view=view,
            ephemeral=True
        )
    
    async def cancel_clicked(self, interaction):
        await interaction.response.send_message("Sélection annulée.", ephemeral=True)
        self.stop()
    
    async def validate_selection(self, interaction):
        if not self.selected_role:
            await interaction.response.send_message("Veuillez d'abord sélectionner un rôle!", ephemeral=True)
            return
        
        # Parse l'emoji
        emoji_str, emoji_display = self.parent_view.cog.parse_emoji(self.selected_emoji)
        
        # Ajouter la paire à la vue parente
        self.parent_view.role_emoji_pairs.append(
            RoleEmojiPair(self.selected_role, emoji_str, emoji_display)
        )
        
        # Mise à jour du message
        await self.parent_view.update_message(interaction)
        await interaction.response.send_message(
            f"✅ Ajouté: {emoji_display} → {self.selected_role.mention}", 
            ephemeral=True
        )
        self.stop()

# Modal pour les emojis personnalisés
class CustomEmojiModal(discord.ui.Modal, title="Emoji personnalisé"):
    def __init__(self, parent_view):
        super().__init__()
        self.parent_view = parent_view
        
        self.emoji_input = discord.ui.TextInput(
            label="Emoji personnalisé",
            placeholder="Collez un emoji personnalisé ici (<:nom:id>)",
            required=True,
            max_length=100
        )
        self.add_item(self.emoji_input)
    
    async def on_submit(self, interaction):
        self.parent_view.selected_emoji = self.emoji_input.value
        await self.parent_view.validate_selection(interaction)

class RoleSetupView(discord.ui.View):
    def __init__(self, user, title, description):
        super().__init__(timeout=600)  # 10 minutes timeout
        self.user = user
        self.title = title
        self.description = description
        self.role_emoji_pairs = []
        self.cog = None  # Sera défini lors de l'appel depuis la commande

    async def interaction_check(self, interaction):
        if interaction.user != self.user:
            await interaction.response.send_message("Vous ne pouvez pas utiliser cette interface.", ephemeral=True)
            return False
        return True
    
    def create_preview_embed(self):
        """Crée l'embed de prévisualisation"""
        embed = discord.Embed(title=self.title, color=discord.Color.blue())
        
        if self.description:
            embed.description = self.description + "\n\n"
        else:
            embed.description = ""
            
        # Ajoute chaque paire rôle/emoji
        for pair in self.role_emoji_pairs:
            embed.description += f"{pair.emoji_display} → {pair.role.mention}\n"
            
        if not self.role_emoji_pairs:
            embed.description += "*Aucun rôle configuré. Utilisez le bouton 'Ajouter un rôle' pour commencer.*"
            
        embed.set_footer(text="Prévisualisation - Utilisez 'Publier' pour finaliser")
        return embed
    
    async def update_message(self, interaction):
        """Met à jour le message avec la prévisualisation actuelle"""
        embed = self.create_preview_embed()
        if interaction.response.is_done():
            await interaction.edit_original_response(content="Configuration des rôles :", embed=embed, view=self)
        else:
            await interaction.response.edit_message(content="Configuration des rôles :", embed=embed, view=self)
    
    @discord.ui.button(label="Ajouter un rôle", style=discord.ButtonStyle.green, row=0)
    async def add_role(self, interaction, button):
        """Ouvre l'interface unifiée de sélection de rôle/emoji"""
        view = UnifiedRoleEmojiView(self)
        view.cog = self.cog  # Passer la référence au cog
        
        await interaction.response.send_message(
            "Sélectionnez un rôle et un emoji:", 
            view=view,
            ephemeral=True
        )
    
    @discord.ui.button(label="Supprimer le dernier", style=discord.ButtonStyle.red, row=0)
    async def remove_last(self, interaction, button):
        """Supprime la dernière paire rôle/emoji ajoutée"""
        if not self.role_emoji_pairs:
            return await interaction.response.send_message("Aucun rôle à supprimer.", ephemeral=True)
            
        removed = self.role_emoji_pairs.pop()
        await self.update_message(interaction)
        await interaction.response.send_message(
            f"✅ Supprimé: {removed.emoji_display} → {removed.role.mention}", 
            ephemeral=True
        )
    
    @discord.ui.button(label="Publier", style=discord.ButtonStyle.primary, row=1)
    async def publish(self, interaction, button):
        """Publie le message de rôles-réactions"""
        if not self.role_emoji_pairs:
            return await interaction.response.send_message(
                "❌ Ajoutez au moins un rôle avant de publier.", 
                ephemeral=True
            )
            
        # Créer l'embed final
        embed = discord.Embed(title=self.title, color=discord.Color.blue())
        if self.description:
            embed.description = self.description + "\n\n"
        else:
            embed.description = ""
            
        for pair in self.role_emoji_pairs:
            embed.description += f"{pair.emoji_display} → {pair.role.mention}\n"
        
        # Envoyer le message
        await interaction.response.send_message("✅ Message de rôles créé!", ephemeral=True)
        message = await interaction.channel.send(embed=embed)
        
        # Ajouter les réactions et enregistrer dans le cog
        self.cog.role_messages[message.id] = {}
        
        for pair in self.role_emoji_pairs:
            try:
                if pair.emoji_str.startswith('<') and ':' in pair.emoji_str:
                    # Pour les émojis personnalisés
                    try:
                        # Extraction de l'ID de l'emoji
                        if pair.emoji_str.startswith('<a:'): # Emoji animé
                            name, emoji_id = pair.emoji_str.strip('<a:>').rsplit(':', 1)
                            emoji_id = int(emoji_id.rstrip('>'))
                            emoji = discord.utils.get(interaction.guild.emojis, id=emoji_id)
                        else: # Emoji normal
                            name, emoji_id = pair.emoji_str.strip('<:>').rsplit(':', 1)
                            emoji_id = int(emoji_id.rstrip('>'))
                            emoji = discord.utils.get(interaction.guild.emojis, id=emoji_id)
                        
                        if emoji:
                            await message.add_reaction(emoji)
                            stored_emoji = str(emoji)
                        else:
                            print(f"Emoji {name} ({emoji_id}) non trouvé sur le serveur")
                            continue
                    except Exception as e:
                        print(f"Erreur lors de l'ajout de la réaction {pair.emoji_str}: {e}")
                        continue
                else:
                    # Pour les émojis Unicode
                    await message.add_reaction(pair.emoji_str)
                    stored_emoji = pair.emoji_str
                
                self.cog.role_messages[message.id][stored_emoji] = pair.role.id
                
            except Exception as e:
                print(f"Erreur lors de l'ajout de la réaction {pair.emoji_str}: {e}")
                
        self.stop()

    @discord.ui.button(label="Annuler", style=discord.ButtonStyle.secondary, row=1)
    async def cancel(self, interaction, button):
        """Annule la configuration"""
        await interaction.response.send_message("Configuration annulée.", ephemeral=True)
        self.stop()

    async def update_message_direct(self):
        """Met à jour le message principal sans passer par une interaction"""
        # Cette méthode sera appelée directement pour éviter les conflits d'interaction
        pass  # Pour l'instant, on peut laisser vide ou implémenter une logique spécifique

class RoleReaction(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        # Format: {message_id: {emoji_id_or_unicode: role_id}}
        self.role_messages: Dict[int, Dict[str, int]] = {}

    def parse_emoji(self, emoji_str: str) -> tuple[str, str]:
        """
        Parse un emoji personnalisé ou unicode
        Retourne (emoji_str, emoji_display)
        """
        # Si c'est un emoji personnalisé (<:name:id>)
        if emoji_str.startswith('<:') and emoji_str.endswith('>'):
            try:
                name, id = emoji_str.strip('<:>').rsplit(':', 1)
                return emoji_str, f"<:{name}:{id}>"
            except ValueError:
                return emoji_str, emoji_str
        # Si c'est un emoji animé (<a:name:id>)
        elif emoji_str.startswith('<a:') and emoji_str.endswith('>'):
            try:
                name, id = emoji_str.strip('<a:>').rsplit(':', 1)
                return emoji_str, f"<a:{name}:{id}>"
            except ValueError:
                return emoji_str, emoji_str
        return emoji_str, emoji_str

    @app_commands.command(
        name="setup_roles_ui",
        description="Crée un message interactif pour attribuer des rôles avec des réactions (interface améliorée)"
    )
    @app_commands.default_permissions(administrator=True)
    async def setup_roles_ui(self, interaction: discord.Interaction):
        """Configuration des rôles-réactions avec une interface utilisateur améliorée"""
        # Vérifie la permission administrateur
        if not interaction.user.guild_permissions.administrator:
            return await interaction.response.send_message("🚫 Vous n'avez pas la permission", ephemeral=True)

        # Ouvrir le modal de configuration
        modal = RoleSetupModal()
        await interaction.response.send_modal(modal)

    # Garder l'ancienne commande pour compatibilité
    @app_commands.command(
        name="setup_roles",
        description="Creates a message enabling several roles to be obtained via several reactions."
    )
    @app_commands.describe(
        roles="List of roles (mentions) separated by a comma, e.g: @Role1, @Role2",
        emojis="List of emojis (custom or unicode) separated by a comma, e.g.: ✅,❌,<:custom:123456789>"
    )
    async def setup_roles(
        self,
        interaction: discord.Interaction,
        roles: str,
        emojis: str
    ):
        # Vérifie la permission administrateur
        if not interaction.user.guild_permissions.administrator:
            return await interaction.response.send_message("🚫 You do not have permission", ephemeral=True)

        # Convertit les chaînes de rôles et d'emojis en listes
        role_mentions = [r.strip() for r in roles.split(',')]
        emoji_list = [e.strip() for e in emojis.split(',')]
        parsed_emojis = [self.parse_emoji(e) for e in emoji_list]

        # Vérifie que le nombre de rôles et d'emojis correspond
        if len(role_mentions) != len(emoji_list):
            return await interaction.response.send_message(
                f"Please provide as many emojis as you have roles.\n"
                f"Rôles: {len(role_mentions)} | Emojis: {len(emoji_list)}",
                ephemeral=True
            )

        embed = discord.Embed(
            title="Assigning roles",
            description=""
        )

        # Essayez de récupérer les objets Role depuis les mentions
        guild = interaction.guild
        parsed_roles: List[discord.Role] = []
        for r_mention in role_mentions:
            # Récupère l'ID du rôle depuis la mention <@&...>
            role_id = r_mention.replace("<@&", "").replace(">", "").strip()
            role_obj = guild.get_role(int(role_id)) if role_id.isdigit() else None
            if role_obj:
                parsed_roles.append(role_obj)
            else:
                return await interaction.response.send_message(
                    f"Rôle `{r_mention}` is missing.",
                    ephemeral=True
                )

        # Construit le message d'explication
        for i, role_obj in enumerate(parsed_roles):
            emoji_str, emoji_display = parsed_emojis[i]
            embed.description += f"{emoji_display} → {role_obj.mention}\n"

        # Envoie le message
        message = await interaction.channel.send(embed=embed)
        self.role_messages[message.id] = {}

        # Ajoute chaque couple (emoji -> role)
        for i, role_obj in enumerate(parsed_roles):
            try:
                emoji_str, emoji_display = parsed_emojis[i]
                if emoji_str.startswith('<') and ':' in emoji_str:
                    # Pour les émojis personnalisés
                    try:
                        # Extraction de l'ID de l'emoji
                        if emoji_str.startswith('<a:'): # Emoji animé
                            name, emoji_id = emoji_str.strip('<a:>').rsplit(':', 1)
                            emoji_id = int(emoji_id.rstrip('>'))
                            # Cherche l'emoji dans le serveur
                            emoji = discord.utils.get(interaction.guild.emojis, id=emoji_id)
                            if not emoji:
                                print(f"Emoji {name} ({emoji_id}) non trouvé sur le serveur")
                                continue
                        else: # Emoji normal
                            name, emoji_id = emoji_str.strip('<:>').rsplit(':', 1)
                            emoji_id = int(emoji_id.rstrip('>'))
                            # Cherche l'emoji dans le serveur
                            emoji = discord.utils.get(interaction.guild.emojis, id=emoji_id)
                            if not emoji:
                                print(f"Emoji {name} ({emoji_id}) non trouvé sur le serveur")
                                continue
                        
                        await message.add_reaction(emoji)
                    except (ValueError, discord.HTTPException) as e:
                        print(f"Erreur lors de l'ajout de la réaction {emoji_str}: {e}")
                        continue
                else:
                    # Pour les émojis Unicode
                    await message.add_reaction(emoji_str)
                
                # Stocke l'emoji sous sa forme complète pour la comparaison plus tard
                if isinstance(emoji, discord.Emoji):
                    stored_emoji = str(emoji)
                else:
                    stored_emoji = emoji_str
                self.role_messages[message.id][stored_emoji] = role_obj.id
                
            except Exception as e:
                print(f"Erreur lors de l'ajout de la réaction {emoji_str}: {e}")
                continue

        await interaction.response.send_message("Done!", ephemeral=True)

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload: discord.RawReactionActionEvent):
        if payload.message_id not in self.role_messages:
            return

        # Gestion des émojis personnalisés et Unicode
        if payload.emoji.id:
            emoji_str = f"<:{payload.emoji.name}:{payload.emoji.id}>"
        else:
            emoji_str = str(payload.emoji)

        if emoji_str in self.role_messages[payload.message_id]:
            guild = self.bot.get_guild(payload.guild_id)
            role = guild.get_role(self.role_messages[payload.message_id][emoji_str])
            member = await guild.fetch_member(payload.user_id)
            if member and member.id != self.bot.user.id:
                await member.add_roles(role)

    @commands.Cog.listener()
    async def on_raw_reaction_remove(self, payload: discord.RawReactionActionEvent):
        if payload.message_id not in self.role_messages:
            return

        # Gestion des émojis personnalisés et Unicode
        if payload.emoji.id:
            emoji_str = f"<:{payload.emoji.name}:{payload.emoji.id}>"
        else:
            emoji_str = str(payload.emoji)

        if emoji_str in self.role_messages[payload.message_id]:
            guild = self.bot.get_guild(payload.guild_id)
            role = guild.get_role(self.role_messages[payload.message_id][emoji_str])
            member = await guild.fetch_member(payload.user_id)
            if member and member.id != self.bot.user.id:
                await member.remove_roles(role)

# Nouvelle classe pour afficher les émojis du serveur
class ServerEmojiSelectionView(discord.ui.View):
    def __init__(self, parent_view):
        super().__init__(timeout=300)
        self.parent_view = parent_view
        self.current_page = 0
        self.server_emojis = []
        self.max_per_page = 20  # 4 lignes de 5 émojis
        
        # Chargement asynchrone des emojis du serveur
        self.setup_buttons_later = True
    
    async def setup_buttons(self, interaction):
        """Configure les boutons d'émojis après l'initialisation"""
        # Récupérer tous les émoïs du serveur
        self.server_emojis = list(interaction.guild.emojis)
        if not self.server_emojis:
            await interaction.edit_original_response(
                content="Ce serveur ne possède aucun emoji personnalisé.", 
                view=None
            )
            return False
            
        # Ajouter les boutons d'émojis pour la page courante
        await self.update_emoji_buttons(interaction)
        # Ajouter les boutons de navigation
        await self.update_navigation_buttons(interaction)
        return True
        
    async def update_emoji_buttons(self, interaction):
        """Mettre à jour les boutons d'émojis selon la page actuelle"""
        # Supprimer tous les boutons d'émojis existants
        self.clear_items()
        
        # Calculer la plage d'émojis pour cette page
        start_idx = self.current_page * self.max_per_page
        end_idx = min(start_idx + self.max_per_page, len(self.server_emojis))
        emojis_to_show = self.server_emojis[start_idx:end_idx]
        
        # Organiser les émojis en grille (4 lignes de 5 max)
        for i, emoji in enumerate(emojis_to_show):
            row = i // 5  # 5 émojis par ligne
            button = discord.ui.Button(
                emoji=emoji,
                style=discord.ButtonStyle.secondary,
                row=row
            )
            button.callback = self.create_emoji_callback(emoji)
            self.add_item(button)
        
        # Ajouter les boutons de navigation
        await self.update_navigation_buttons(interaction)
    
    async def update_navigation_buttons(self, interaction=None):
        """Mettre à jour les boutons de navigation"""
        # Nombre total de pages
        total_pages = (len(self.server_emojis) + self.max_per_page - 1) // self.max_per_page
        
        # Boutons de navigation (sur la dernière ligne)
        row = 4
        
        # Bouton précédent
        prev_button = discord.ui.Button(
            label="◀️ Précédent",
            style=discord.ButtonStyle.primary,
            disabled=(self.current_page == 0),
            row=row
        )
        prev_button.callback = self.previous_page
        self.add_item(prev_button)
        
        # Indicateur de page
        page_indicator = discord.ui.Button(
            label=f"Page {self.current_page + 1}/{total_pages}",
            disabled=True,
            row=row
        )
        self.add_item(page_indicator)
        
        # Bouton suivant
        next_button = discord.ui.Button(
            label="Suivant ▶️",
            style=discord.ButtonStyle.primary,
            disabled=(self.current_page >= total_pages - 1),
            row=row
        )
        next_button.callback = self.next_page
        self.add_item(next_button)
        
        # Bouton annuler
        cancel_button = discord.ui.Button(
            label="Annuler",
            style=discord.ButtonStyle.danger,
            row=row
        )
        cancel_button.callback = self.cancel
        self.add_item(cancel_button)
    
    def create_emoji_callback(self, emoji):
        async def emoji_callback(interaction):
            # Stocker l'emoji sélectionné dans la vue parente
            self.parent_view.selected_emoji = str(emoji)
            # Valider la sélection
            await self.parent_view.validate_selection(interaction)
            # Fermer cette vue
            self.stop()
        return emoji_callback
    
    async def previous_page(self, interaction):
        """Page précédente d'émojis"""
        self.current_page -= 1
        await self.update_emoji_buttons(interaction)
        await interaction.response.edit_message(view=self)
    
    async def next_page(self, interaction):
        """Page suivante d'émojis"""
        self.current_page += 1
        await self.update_emoji_buttons(interaction)
        await interaction.response.edit_message(view=self)
    
    async def cancel(self, interaction):
        """Annuler la sélection"""
        await interaction.response.send_message("Sélection annulée.", ephemeral=True)
        self.stop()
    
    async def interaction_check(self, interaction):
        """Vérifie si l'interaction est autorisée"""
        if self.setup_buttons_later:
            self.setup_buttons_later = False
            success = await self.setup_buttons(interaction)
            if not success:
                return False
        return True

# Une nouvelle classe qui combine la sélection de rôle et d'emoji dans une seule vue
class UnifiedRoleEmojiView(discord.ui.View):
    def __init__(self, parent_view):
        super().__init__(timeout=300)
        self.parent_view = parent_view
        self.selected_role = None
        self.selected_emoji = None
        self.emoji_type = "standard"
        self.current_page = 0
        self.server_emojis = []
        self.max_per_page = 10
        
        # Configuration de l'interface
        self.setup_interface()

    def setup_interface(self):
        """Configuration initiale de l'interface"""
        # Ligne 0: Bouton de sélection de rôle
        self.role_button = discord.ui.Button(
            label="📋 Sélectionner un rôle",
            style=discord.ButtonStyle.primary,
            row=0
        )
        self.role_button.callback = self.open_role_modal
        self.add_item(self.role_button)
        
        # Ligne 1: Onglets
        self.add_emoji_tabs()
        
        # Lignes 2-3: Émojis (ajoutés par les méthodes spécialisées)
        self.update_standard_emojis()
        
        # Ligne 4: Confirmation et annulation seulement
        self.confirm_button = discord.ui.Button(
            emoji="✅", 
            style=discord.ButtonStyle.success,
            disabled=True,
            row=4
        )
        self.confirm_button.callback = self.confirm_selection
        self.add_item(self.confirm_button)

        self.cancel_button = discord.ui.Button(
            emoji="❌", 
            style=discord.ButtonStyle.danger,
            row=4
        )
        self.cancel_button.callback = self.cancel_selection
        self.add_item(self.cancel_button)
    
    async def open_role_modal(self, interaction):
        """Ouvre le modal de sélection de rôle"""
        modal = RoleSelectionModal(self)
        await interaction.response.send_modal(modal)
    
    def add_emoji_tabs(self):
        """Ajouter les boutons d'onglets pour les types d'émojis"""
        self.standard_tab = discord.ui.Button(
            label="Standard", 
            style=discord.ButtonStyle.primary if self.emoji_type == "standard" else discord.ButtonStyle.secondary,
            row=1
        )
        self.standard_tab.callback = self.switch_to_standard
        self.add_item(self.standard_tab)
        
        self.server_tab = discord.ui.Button(
            label="Serveur", 
            style=discord.ButtonStyle.primary if self.emoji_type == "server" else discord.ButtonStyle.secondary,
            row=1
        )
        self.server_tab.callback = self.switch_to_server
        self.add_item(self.server_tab)
    
    def update_standard_emojis(self):
        """Afficher les émojis standard"""
        # Émojis standards sur 2 lignes seulement
        self.common_emojis = [
            ["😀", "😂", "😍", "🥰", "😎"],  # Ligne 2
            ["✅", "❌", "⭐", "🔥", "💯"]   # Ligne 3
        ]
        
        # Ajouter les boutons d'émojis
        for row_idx, emoji_row in enumerate(self.common_emojis):
            for emoji in emoji_row:
                button = discord.ui.Button(
                    emoji=emoji, 
                    style=discord.ButtonStyle.secondary,
                    row=row_idx + 2  # Lignes 2 et 3
                )
                button.callback = self.create_standard_emoji_callback(emoji)
                self.add_item(button)
    
    async def update_server_emojis(self, interaction):
        """Afficher les émojis du serveur"""
        self.server_emojis = list(interaction.guild.emojis)
        
        if not self.server_emojis:
            info_button = discord.ui.Button(
                label="Aucun emoji personnalisé", 
                disabled=True,
                row=2
            )
            self.add_item(info_button)
            return
        
        # Calculer la plage d'émojis pour cette page
        start_idx = self.current_page * self.max_per_page
        end_idx = min(start_idx + self.max_per_page, len(self.server_emojis))
        emojis_to_show = self.server_emojis[start_idx:end_idx]
        
        # Ajouter les émojis (2 lignes de 5 max)
        for i, emoji in enumerate(emojis_to_show):
            row = 2 + (i // 5)  # Lignes 2 et 3 seulement
            if row > 3:
                break
            button = discord.ui.Button(
                emoji=emoji, 
                style=discord.ButtonStyle.secondary,
                row=row
            )
            button.callback = self.create_server_emoji_callback(emoji)
            self.add_item(button)
        
        # Navigation sur ligne 1 (avec les onglets) si nécessaire
        if len(self.server_emojis) > self.max_per_page:
            total_pages = (len(self.server_emojis) + self.max_per_page - 1) // self.max_per_page
            
            # Navigation compacte sur ligne 1
            if self.current_page > 0:
                prev_button = discord.ui.Button(
                    emoji="◀️", 
                    style=discord.ButtonStyle.secondary,
                    row=1
                )
                prev_button.callback = self.prev_page
                self.add_item(prev_button)
            
            if self.current_page < total_pages - 1:
                next_button = discord.ui.Button(
                    emoji="▶️", 
                    style=discord.ButtonStyle.secondary,
                    row=1
                )
                next_button.callback = self.next_page
                self.add_item(next_button)
            
            # Indicateur de page compact
            page_button = discord.ui.Button(
                label=f"{self.current_page + 1}/{total_pages}", 
                disabled=True,
                row=1
            )
            self.add_item(page_button)
    
    def create_standard_emoji_callback(self, emoji):
        async def callback(interaction):
            self.selected_emoji = emoji
            await self.update_view_state(interaction)
        return callback
    
    def create_server_emoji_callback(self, emoji):
        async def callback(interaction):
            self.selected_emoji = str(emoji)
            await self.update_view_state(interaction)
        return callback
    
    async def switch_to_standard(self, interaction):
        """Basculer vers l'onglet des émojis standard"""
        self.emoji_type = "standard"
        self.clear_items()
        
        # Reconstruire l'interface
        self.setup_interface()
        
        await interaction.response.edit_message(view=self)
    
    async def switch_to_server(self, interaction):
        """Basculer vers l'onglet des émojis du serveur"""
        self.emoji_type = "server"
        self.clear_items()
        
        # Reconstruire l'interface sans les émojis standard
        # Ligne 0: Bouton de sélection de rôle
        self.add_item(self.role_button)
        
        # Ligne 1: Onglets
        self.add_emoji_tabs()
        
        # Lignes 2-3: Émojis du serveur
        await self.update_server_emojis(interaction)
        
        # Ligne 4: Confirmation et annulation
        self.add_item(self.confirm_button)
        self.add_item(self.cancel_button)
        
        await interaction.response.edit_message(view=self)
    
    async def prev_page(self, interaction):
        """Page précédente d'émojis du serveur"""
        self.current_page -= 1
        await self.switch_to_server(interaction)
    
    async def next_page(self, interaction):
        """Page suivante d'émojis du serveur"""
        self.current_page += 1
        await self.switch_to_server(interaction)
    
    async def update_view_state(self, interaction):
        """Mettre à jour l'état de la vue en fonction des sélections"""
        self.confirm_button.disabled = not (self.selected_role and self.selected_emoji)
        
        # Mettre à jour le texte du bouton de rôle
        if self.selected_role:
            self.role_button.label = f"✅ {self.selected_role.name}"
            self.role_button.style = discord.ButtonStyle.success
        
        content = "Sélectionnez un rôle et un emoji:"
        if self.selected_role:
            content += f"\n✅ Rôle: {self.selected_role.mention}"
        if self.selected_emoji:
            content += f"\n✅ Emoji: {self.selected_emoji}"
        
        # Vérifier si l'interaction a déjà été répondue
        if interaction.response.is_done():
            await interaction.edit_original_response(content=content, view=self)
        else:
            await interaction.response.edit_message(content=content, view=self)
    
    async def confirm_selection(self, interaction):
        """Confirmer la sélection et ajouter la paire rôle/emoji"""
        if not self.selected_role or not self.selected_emoji:
            await interaction.response.send_message("Sélectionnez un rôle et un emoji.", ephemeral=True)
            return
        
        emoji_str, emoji_display = self.parent_view.cog.parse_emoji(self.selected_emoji)
        
        self.parent_view.role_emoji_pairs.append(
            RoleEmojiPair(self.selected_role, emoji_str, emoji_display)
        )
        
        # Répondre immédiatement sans essayer de mettre à jour d'autres messages
        await interaction.response.send_message(
            f"✅ Ajouté: {emoji_display} → {self.selected_role.mention}",
            ephemeral=True
        )
        self.stop()
    
    async def cancel_selection(self, interaction):
        """Annuler la sélection"""
        if interaction.response.is_done():
            await interaction.edit_original_response(content="❌ Sélection annulée.", view=None)
        else:
            await interaction.response.edit_message(content="❌ Sélection annulée.", view=None)
        self.stop()

# Ajoutez cette nouvelle classe Modal pour la sélection de rôles

class RoleSelectionModal(discord.ui.Modal, title='Sélection de rôle'):
    def __init__(self, parent_view):
        super().__init__()
        self.parent_view = parent_view
        
        self.role_input = discord.ui.TextInput(
            label='Nom du rôle',
            placeholder='Tapez le nom du rôle (ex: Membre, Gaming, etc.)',
            required=True,
            max_length=100
        )
        self.add_item(self.role_input)
    
    async def on_submit(self, interaction: discord.Interaction):
        role_name = self.role_input.value.strip()
        
        # Rechercher le rôle par nom (recherche flexible)
        guild = interaction.guild
        found_role = None
        
        # Recherche exacte d'abord
        for role in guild.roles:
            if role.name.lower() == role_name.lower() and role.name != "@everyone":
                found_role = role
                break
        
        # Si pas trouvé, recherche partielle
        if not found_role:
            for role in guild.roles:
                if role_name.lower() in role.name.lower() and role.name != "@everyone":
                    found_role = role
                    break
        
        if not found_role:
            # Afficher les rôles disponibles
            available_roles = [role.name for role in guild.roles 
                             if role.name != "@everyone" and not role.managed][:10]
            role_list = ", ".join(available_roles)
            if len(available_roles) == 10:
                role_list += "..."
            
            await interaction.response.send_message(
                f"❌ Rôle '{role_name}' introuvable.\n"
                f"**Rôles disponibles:** {role_list}",
                ephemeral=True
            )
            return
        
        # Stocker le rôle sélectionné
        self.parent_view.selected_role = found_role
        await self.parent_view.update_view_state(interaction)

async def setup(bot):
    await bot.add_cog(RoleReaction(bot))