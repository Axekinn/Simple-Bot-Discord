import discord
from discord.ext import commands
from discord import app_commands
import asyncio
import traceback
import logging

# Set up logging
logger = logging.getLogger('discord.voice_creator')

class BasicCategorySelect(discord.ui.Select):
    def __init__(self, view, categories):
        self.parent_view = view
        # Generate options for dropdown
        try:
            options = []
            for category in categories[:25]:  # Max 25 options
                options.append(
                    discord.SelectOption(
                        label=category.name[:100],  # Max 100 chars
                        value=str(category.id),
                        description=f"Create in {category.name[:100]}"
                    )
                )
            
            if not options:
                # Fallback option if no categories
                options = [discord.SelectOption(label="Default", value="0", description="Default location")]
            
            super().__init__(placeholder="Choose a category...", options=options)
        except Exception as e:
            logger.error(f"Error initializing category select: {e}\n{traceback.format_exc()}")
            raise
            
    async def callback(self, interaction: discord.Interaction):
        try:
            if interaction.user.id != self.parent_view.user.id:
                await interaction.response.send_message("This is not your control panel", ephemeral=True)
                return
                
            logger.info(f"Category selected: {self.values[0]} by {interaction.user.name}")
            self.parent_view.category_id = int(self.values[0])
            await interaction.response.send_message(f"Category selected! Now choose public or private.", ephemeral=True)
        except Exception as e:
            logger.error(f"Error in category select callback: {e}\n{traceback.format_exc()}")
            await interaction.response.send_message(f"Error selecting category: {str(e)}", ephemeral=True)

class VoiceChannelView(discord.ui.View):
    def __init__(self, cog, user, guild, timeout=60):
        super().__init__(timeout=timeout)
        self.cog = cog
        self.user = user
        self.guild = guild
        self.is_private = False
        self.category_id = None
        
        # Add categories dropdown first
        try:
            categories = [cat for cat in guild.categories 
                        if cat.permissions_for(guild.me).manage_channels]
            
            # If no valid categories, try to use any category
            if not categories:
                categories = guild.categories[:1]
                
            if categories:
                self.add_item(BasicCategorySelect(self, categories))
        except Exception as e:
            logger.error(f"Error setting up channel view: {e}\n{traceback.format_exc()}")
    
    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        # Only allow the target user to interact with these controls
        if interaction.user.id != self.user.id:
            await interaction.response.send_message("This is not your control panel", ephemeral=True)
            return False
        return True
    
    async def on_timeout(self):
        # Handle view timeout
        try:
            for item in self.children:
                item.disabled = True
        except Exception as e:
            logger.error(f"Error in timeout handler: {e}")
    
    # Use the decorator with unique custom_ids
    @discord.ui.button(label="Public Channel", style=discord.ButtonStyle.green, custom_id="public_button")
    async def public_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        try:
            self.is_private = False
            await interaction.response.defer(ephemeral=True)
            
            logger.info(f"Public channel requested by {interaction.user.name}")
            await self._create_channel(interaction)
            self.stop()
        except Exception as e:
            logger.error(f"Error in public button handler: {e}\n{traceback.format_exc()}")
            await interaction.followup.send(f"Error creating channel: {str(e)}", ephemeral=True)
    
    @discord.ui.button(label="Private Channel", style=discord.ButtonStyle.blurple, custom_id="private_button")
    async def private_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        try:
            self.is_private = True
            await interaction.response.defer(ephemeral=True)
            
            logger.info(f"Private channel requested by {interaction.user.name}")
            await self._create_channel(interaction)
            self.stop()
        except Exception as e:
            logger.error(f"Error in private button handler: {e}\n{traceback.format_exc()}")
            await interaction.followup.send(f"Error creating channel: {str(e)}", ephemeral=True)
    
    async def _create_channel(self, interaction):
        try:
            # Get the category
            if self.category_id:
                category = self.guild.get_channel(self.category_id)
                logger.info(f"Using category: {category.name if category else 'None'}")
            else:
                # Use default category if none selected
                category = None
                logger.info("No category selected, using default")
            
            # Create the channel with appropriate settings
            if self.is_private:
                overwrites = {
                    self.guild.default_role: discord.PermissionOverwrite(connect=False, view_channel=True),
                    self.user: discord.PermissionOverwrite(
                        connect=True, 
                        view_channel=True,
                        manage_channels=True,
                        manage_permissions=True,
                        move_members=True,
                        mute_members=True,
                        deafen_members=True
                    )
                }
                
                channel_name = f"{self.user.display_name}'s Private Channel"
                logger.info(f"Creating private channel: {channel_name}")
                channel = await self.guild.create_voice_channel(
                    name=channel_name, 
                    category=category,
                    overwrites=overwrites
                )
                
                feedback = (
                    f"Private channel created in {category.name if category else 'server'}\n"
                    f"You have full control over {channel.mention}\n"
                    "You can right-click the channel to edit permissions and add other users."
                )
            else:
                channel_name = f"{self.user.display_name}'s Channel"
                logger.info(f"Creating public channel: {channel_name}")
                channel = await self.guild.create_voice_channel(
                    name=channel_name, 
                    category=category
                )
                
                # Set permissions for creator
                await channel.set_permissions(self.user, 
                    connect=True, 
                    view_channel=True,
                    manage_channels=True,
                    manage_permissions=True,
                    move_members=True,
                    mute_members=True,
                    deafen_members=True
                )
                
                feedback = (
                    f"Public channel created in {category.name if category else 'server'}\n"
                    f"You have full control over {channel.mention}"
                )
            
            # Track this channel
            self.cog.managed_channels[channel.id] = self.user.id
            logger.info(f"Channel created successfully: {channel.id}")
            
            # Check if user is in a voice channel before moving them
            member = self.guild.get_member(self.user.id)
            if member.voice and member.voice.channel:
                try:
                    # Try to move the user
                    await self.user.move_to(channel)
                    logger.info(f"User moved to new channel: {self.user.name} -> {channel.name}")
                except Exception as e:
                    logger.error(f"Failed to move user to channel: {e}")
                    # Add the join instructions to feedback
                    feedback += f"\n\nJoin your channel by clicking on {channel.mention}"
            else:
                # User is not in voice, just provide the link
                logger.info(f"User {self.user.name} is not in voice, providing channel link")
                feedback += f"\n\nJoin your new channel by clicking on {channel.mention}"
            
            await interaction.followup.send(feedback, ephemeral=True)
            
        except Exception as e:
            logger.error(f"Error creating channel: {e}\n{traceback.format_exc()}")
            await interaction.followup.send(
                f"Error creating your channel: {str(e)}\n"
                "Please make sure the bot has proper permissions.",
                ephemeral=True
            )

class VoiceCreator(commands.Cog):
    """Handles dynamic voice channel creation."""
    
    def __init__(self, bot):
        self.bot = bot
        self.managed_channels = {}  # channel_id: owner_id
        self.creator_channels = {}  # creator_channel_id: category_id
        self.embed_color = 0xBEBEFE  # Standard color
        logger.info("Voice Creator cog initialized")
    
    @commands.Cog.listener()
    async def on_voice_state_update(self, member, before, after):
        """Monitors voice state changes to create/delete channels."""
        try:
            # Ignore if bot
            if member.bot:
                return
                
            # Logging all channel IDs for debugging
            logger.debug(f"Creator channels: {self.creator_channels.keys()}")
            logger.debug(f"Managed channels: {self.managed_channels.keys()}")
                
            # Handle channel creation when a user joins the creator channel
            if after.channel and after.channel.id in self.creator_channels:
                # User joined a creator channel
                logger.info(f"User {member.name} ({member.id}) joined creator channel {after.channel.id}")
                
                # Get the category from the creator channel
                category_id = self.creator_channels[after.channel.id]
                category = self.bot.get_channel(category_id) if category_id else None
                
                # Create a new voice channel in the same category
                channel_name = f"Salon de {member.display_name}"
                
                logger.info(f"Creating voice channel: {channel_name}")
                new_channel = await member.guild.create_voice_channel(
                    name=channel_name, 
                    category=category
                )
                
                # Track this channel as a user-created channel
                self.managed_channels[new_channel.id] = member.id
                # NE PAS ajouter le salon créateur à managed_channels !
                logger.info(f"Channel created successfully: {new_channel.id}")
                
                # Move user to the new channel
                try:
                    await member.move_to(new_channel)
                    logger.info(f"User moved to new channel: {member.name} -> {new_channel.name}")
                    
                    # Set permissions for creator
                    await new_channel.set_permissions(member, 
                        connect=True, 
                        view_channel=True,
                        manage_channels=True,
                        manage_permissions=True,
                        move_members=True,
                        mute_members=True,
                        deafen_members=True
                    )
                except Exception as e:
                    logger.error(f"Error moving user to channel: {e}")
                    
            # Handle channel deletion if empty
            if before.channel:
                # NE JAMAIS supprimer un salon créateur
                if before.channel.id in self.creator_channels:
                    logger.warning(f"Attempted to delete creator channel {before.channel.id}, skipping.")
                    # Nettoyage si jamais il s'est retrouvé dans managed_channels
                    if before.channel.id in self.managed_channels:
                        del self.managed_channels[before.channel.id]
                    return

                if before.channel.id in self.managed_channels:
                    await asyncio.sleep(1)
                    channel = self.bot.get_channel(before.channel.id)
                    if channel and len(channel.members) == 0:
                        try:
                            logger.info(f"Auto-deleting empty channel {channel.name} ({channel.id})")
                            await channel.delete(reason="Auto-deletion: Channel empty")
                            del self.managed_channels[channel.id]
                        except Exception as e:
                            logger.error(f"Error deleting channel {channel.id}: {e}")

        except Exception as e:
            logger.error(f"Error in voice state update handler: {e}\n{traceback.format_exc()}")
    
    async def get_system_channel(self, guild):
        """Gets an appropriate channel to send system messages."""
        try:
            # Try guild's system channel first
            if guild.system_channel and guild.system_channel.permissions_for(guild.me).send_messages:
                return guild.system_channel
                
            # Otherwise find first text channel bot can send to
            for channel in guild.text_channels:
                if channel.permissions_for(guild.me).send_messages:
                    return channel
        except Exception as e:
            logger.error(f"Error finding system channel: {e}")
            
        # If all else fails
        return None
    
    @app_commands.command(
        name="setup_voice_creator",
        description="Set up a voice channel that automatically creates new channels when joined"
    )
    @app_commands.describe(
        name="Name of the creator channel",
        category="Category to place created channels in (optional)"
    )
    @app_commands.default_permissions(administrator=True)
    async def setup_voice_creator(self, interaction: discord.Interaction, name: str = "➕ Create Channel", category: discord.CategoryChannel = None):
        """Sets up the voice channel creator system."""
        try:
            # Create a new voice channel that will act as the creator
            creator_channel = await interaction.guild.create_voice_channel(
                name=name,
                category=category
            )
            
            # Track this channel
            if category:
                self.creator_channels[creator_channel.id] = category.id
            else:
                # If no category specified, use the same one as the creator channel
                self.creator_channels[creator_channel.id] = creator_channel.category_id if creator_channel.category else None
            
            logger.info(f"Set up voice creator channel {creator_channel.id} in guild {interaction.guild.id}")
            
            embed = discord.Embed(
                title="Voice Creator Setup Complete",
                description=f"I've created a new voice channel: {creator_channel.mention}\n\n"
                        f"When users join this channel, they'll be able to create their own voice channel.",
                color=self.embed_color
            )
            
            await interaction.response.send_message(embed=embed, ephemeral=True)
            
        except Exception as e:
            logger.error(f"Error setting up voice creator: {e}\n{traceback.format_exc()}")
            await interaction.response.send_message(
                f"Error setting up voice creator: {str(e)}\n"
                "Please make sure the bot has the necessary permissions.",
                ephemeral=True
            )

async def setup(bot):
    try:
        await bot.add_cog(VoiceCreator(bot))
        logger.info("Voice Creator cog loaded successfully")
    except Exception as e:
        logger.error(f"Failed to load Voice Creator cog: {e}\n{traceback.format_exc()}")
        raise