import discord
from discord.ext import commands
from discord import app_commands
from datetime import datetime
import re

class Vote(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    def convert_date(self, date):
        return date.strftime("%d/%m/%Y à %H:%M:%S")

    def display_name_and_id(self, member):
        return f"{member.display_name} ({member.id})"

    def str_to_bool(self, value):
        true_values = ['yes', 'true', '1', 'oui', 'vrai']
        false_values = ['no', 'false', '0', 'non', 'faux']
        
        value = value.lower()
        if value in true_values:
            return True
        elif value in false_values:
            return False
        else:
            raise commands.BadArgument("Valeur invalide. Utilisez oui/non, true/false, 1/0")

    @app_commands.command(name="vote_create", description="Crée un vote")
    @app_commands.describe(anonyme="Vote anonyme ?", thread="Créer un thread associé ?", proposition="Proposition de vote")
    async def vote_create(self, interaction: discord.Interaction, anonyme: bool, thread: bool, proposition: str):
        """Crée un vote"""
        embed = discord.Embed(
            color=discord.Color.green(),
            title="Nouveau vote"
        )
        embed.add_field(name="Proposition", value=f"```{proposition}```")
        embed.set_author(
            name=self.display_name_and_id(interaction.user),
            icon_url=interaction.user.display_avatar.url
        )
        embed.set_footer(text=f"Vote posté le {self.convert_date(datetime.now())}")

        if anonyme:
            buttons = discord.ui.View()
            buttons.add_item(discord.ui.Button(emoji="✅", custom_id="yes", style=discord.ButtonStyle.secondary))
            buttons.add_item(discord.ui.Button(emoji="⌛", custom_id="wait", style=discord.ButtonStyle.secondary))
            buttons.add_item(discord.ui.Button(emoji="❌", custom_id="no", style=discord.ButtonStyle.secondary))
            
            embed.description = "✅ : 0\n⌛ : 0\n❌ : 0"
            await interaction.response.send_message(embed=embed, view=buttons)
        else:
            await interaction.response.send_message(embed=embed)
            message = await interaction.original_response()
            await message.add_reaction("✅")
            await message.add_reaction("⌛")
            await message.add_reaction("❌")

        if thread:
            thread = await message.create_thread(
                name=f"Vote de {interaction.user.name}",
                auto_archive_duration=1440
            )
            await thread.add_user(interaction.user)

    @app_commands.command(name="vote_edit", description="Modifie un vote existant")
    @app_commands.describe(message_id="ID du message de vote", new_proposition="Nouvelle proposition de vote")
    async def vote_edit(self, interaction: discord.Interaction, message_id: str, new_proposition: str):
        """Modifie un vote existant"""
        if not re.match(r"^\d{17,19}$", message_id):
            return await interaction.response.send_message("ID de message invalide", ephemeral=True)

        try:
            message = await interaction.channel.fetch_message(int(message_id))
        except discord.NotFound:
            return await interaction.response.send_message("Message non trouvé dans ce salon", ephemeral=True)

        if not message.author == self.bot.user or not message.embeds:
            return await interaction.response.send_message("Ce message n'est pas un vote", ephemeral=True)

        original_embed = message.embeds[0]
        if interaction.user.id != int(re.search(r"\((\d+)\)", original_embed.author.name).group(1)):
            return await interaction.response.send_message("Vous n'êtes pas l'auteur de ce vote", ephemeral=True)

        new_embed = discord.Embed(
            color=discord.Color.green(),
            title="Nouveau vote (modifié)"
        )
        new_embed.add_field(name="Proposition", value=f"```{new_proposition}```")
        new_embed.set_author(
            name=self.display_name_and_id(interaction.user),
            icon_url=interaction.user.display_avatar.url
        )
        new_embed.set_footer(
            text=f"Vote posté le {original_embed.footer.text.split('posté le ')[1]}\n"
                f"Modifié le {self.convert_date(datetime.now())}"
        )

        if hasattr(original_embed, "description"):
            new_embed.description = original_embed.description

        await message.edit(embed=new_embed)
        await interaction.response.send_message("Proposition de vote modifiée 👌", ephemeral=True)

async def setup(bot):
    await bot.add_cog(Vote(bot))
    await bot.tree.sync()  # Ensure the commands are registered with Discord