"""
Copyright © Krypton 2019-Present - https://github.com/kkrypt0nn (https://krypton.ninja)
Description:
🐍 Un modèle simple pour commencer à coder votre propre bot Discord personnalisé en Python

Version: 6.2.0
"""

import platform
import random

import aiohttp
import discord
from discord import app_commands
from discord.ext import commands
from discord.ext.commands import Context


class FeedbackForm(discord.ui.Modal):
    def __init__(self):
        super().__init__(title="Feedback")
    feedback = discord.ui.TextInput(
        label="What do you think of this bot?",
        style=discord.TextStyle.long,
        placeholder="Type your answer here...",
        required=True,
        max_length=256,
    )

    async def on_submit(self, interaction: discord.Interaction):
        """
        Gère la soumission du formulaire de retour d'information.

        :param interaction: L'interaction qui a déclenché la soumission.
        """
        self.interaction = interaction
        self.answer = str(self.feedback)
        self.stop()


class General(commands.Cog, name="general"):
    def __init__(self, bot) -> None:
        self.bot = bot
        self.context_menu_user = app_commands.ContextMenu(
            name="Get ID", callback=self.grab_id
        )
        self.bot.tree.add_command(self.context_menu_user)
        self.context_menu_message = app_commands.ContextMenu(
            name="Delet Spoiler", callback=self.remove_spoilers
        )
        self.bot.tree.add_command(self.context_menu_message)

    # Commande de menu contextuel de message
    async def remove_spoilers(
        self, interaction: discord.Interaction, message: discord.Message
    ) -> None:
        """
        Supprime les spoilers du message. Cette commande nécessite l'intention MESSAGE_CONTENT pour fonctionner correctement.

        :param interaction: L'interaction de la commande d'application.
        :param message: Le message avec lequel on interagit.
        """
        spoiler_attachment = None
        for attachment in message.attachments:
            if attachment.is_spoiler():
                spoiler_attachment = attachment
                break
        embed = discord.Embed(
            title="Message without spoilers",
            description=message.content.replace("||", ""),
            color=0xBEBEFE,
        )
        if spoiler_attachment is not None:
            embed.set_image(url=attachment.url)
        await interaction.response.send_message(embed=embed, ephemeral=True)

    # Commande de menu contextuel d'utilisateur
    async def grab_id(
        self, interaction: discord.Interaction, user: discord.User
    ) -> None:
        """
        Récupère l'ID de l'utilisateur.

        :param interaction: L'interaction de la commande d'application.
        :param user: L'utilisateur avec lequel on interagit.
        """
        embed = discord.Embed(
            description=f"L'ID of {user.mention} is `{user.id}`.",
            color=0xBEBEFE,
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @commands.hybrid_command(name="help", description="Displays the list of available commands.")
    async def help(self, ctx):
        """
        Affiche la liste des commandes disponibles.

        :param ctx: Le contexte de la commande.
        """
        embed = discord.Embed(title="help", description="Here is the list of available commands:", color=0x00ff00)
        for cog_name, cog in self.bot.cogs.items():
            if cog is not None:
                commands_list = ""
                for command in cog.get_commands():
                    command_name = command.name
                    command_description = command.description if command.description else "No description."
                    commands_list += f"**/{command_name}** - {command_description}\n"
                if commands_list:
                    embed.add_field(name=cog_name.capitalize(), value=commands_list, inline=False)
        await ctx.send(embed=embed)

    @commands.hybrid_command(name="botinfo", description="Get useful information (or not) about the bot.")
    async def botinfo(self, context: commands.Context) -> None:
        """
        Obtenir des informations utiles (ou non) sur le bot.

        :param context: Le contexte de la commande hybride.
        """
        embed = discord.Embed(
            description="Using the model [Krypton](https://krypton.ninja)",
            color=0xBEBEFE,
        )
        embed.set_author(name="Bot information", icon_url=self.bot.user.display_avatar.url)
        embed.add_field(name="Owner:", value="_axekin", inline=True)
        embed.add_field(
            name="Version of python:", value=f"{platform.python_version()}", inline=True
        )
        embed.add_field(
            name="Préfixe:",
            value=f"/ (Commands Slash) or {self.bot.command_prefix} for normal commands",
            inline=False,
        )
        embed.set_footer(text=f"Asked by {context.author}")
        await context.send(embed=embed)

    @commands.hybrid_command(
        name="serverinfo",
        description="Obtain useful information (or not) about the server.",
    )
    async def serverinfo(self, context: commands.Context) -> None:
        """
        Obtenir des informations utiles (ou non) sur le serveur.

        :param context: Le contexte de la commande hybride.
        """
        roles = [role.name for role in context.guild.roles]
        num_roles = len(roles)
        if num_roles > 50:
            roles = roles[:50]
            roles.append(f">>>> Affichage of [50/{num_roles}] rôles")
        await context.send(embed=discord.Embed(title="Server information", description="\n".join(roles), color=0x00ff00))

    @commands.hybrid_command(
        name="ping",
        description="Check if the bot is alive.",
    )
    async def ping(self, context: Context) -> None:
        """
        Vérifier si le bot est vivant.

        :param context: Le contexte de la commande hybride.
        """
        embed = discord.Embed(
            title="🏓 Pong!",
            description=f"The bot's latency time is {round(self.bot.latency * 1000)}ms.",
            color=0xBEBEFE,
        )
        await context.send(embed=embed)

    @commands.hybrid_command(
        name="invite",
        description="Get the bot's invitation link to be able to invite it.",
    )
    async def invite(self, context: Context) -> None:
        """
        Obtenir le lien d'invitation du bot pour pouvoir l'inviter.

        :param context: Le contexte de la commande hybride.
        """
        embed = discord.Embed(
            description=f"Invite me by clicking [here].({self.bot.config['invite_link']}).",
            color=0xD75BF4,
        )
        try:
            await context.author.send(embed=embed)
            await context.send("I sent you a private message!")
        except discord.Forbidden:
            await context.send(embed=embed)

    @commands.hybrid_command(
        name="server",
        description="Get the bot's discord server invitation link for help.",
    )
    async def server(self, context: Context) -> None:
        """
        Obtenez le lien d'invitation du serveur discord du bot pour obtenir de l'aide.

        :param context: Le contexte de la commande hybride.
        """
        embed = discord.Embed(
            description=f"Join the bot support server by clicking [here].(https://discord.com/invite/emulationfr).",
            color=0xD75BF4,
        )
        try:
            await context.author.send(embed=embed)
            await context.send("I sent you a private message!")
        except discord.Forbidden:
            await context.send(embed=embed)

    @commands.hybrid_command(
        name="8ball",
        description="Ask the robot any question.",
    )
    @app_commands.describe(question="The question you want to ask.")
    async def eight_ball(self, context: Context, *, question: str) -> None:
        """
        Posez n'importe quelle question au robot.

        :param context: Le contexte de la commande hybride.
        :param question: La question que vous voulez poser.
        """
        answers = [
            "It is certain.",
            "Without a doubt.",
            "You can count on it.",
            "Yes - definitely.",
            "Very likely.",
            "The outlook is good.",
            "Yes.",
            "Signs point to yes.",
            "Reply hazy, try again.",
            "Ask again later.",
            "Better not tell you now.",
            "Cannot predict now.",
            "Concentrate and ask again.",
            "Don't count on it.",
            "My reply is no.",
            "My sources say no.",
            "The outlook is not so good.",
            "Very doubtful.",
            "Absolutely.",
            "I don't think so.",
            "It's possible.",
            "I can't say now.",
            "It's a certainty.",
            "I'm not sure.",
            "Yes, but with reservations.",
            "No, not at all.",
            "The chances are low.",
            "The chances are high.",
            "I would say yes.",
            "I would say no.",
            "Maybe.",
            "Probably not.",
            "Probably yes.",
            "The signs are hazy.",
            "The signs are clear.",
            "I can't answer now.",
            "Try again.",
            "Ask again later.",
            "I don't know.",
            "I can't predict that.",
            "Absolutely not.",
            "Definitely yes.",
            "It's unclear.",
            "Ask someone else.",
            "The future is uncertain.",
            "Yes, in due time.",
            "No, not now.",
            "Yes, but be cautious.",
            "No, and don't try.",
            "Yes, and go for it.",
            "No, and stay away.",
            "The odds are in your favor.",
            "The odds are against you.",
            "Yes, with effort.",
            "No, without a doubt.",
            "Yes, but it will take time.",
            "No, and it will be difficult.",
            "Yes, and it will be easy.",
            "No, and it will be hard.",
            "Yes, and it will be worth it.",
            "No, and it won't be worth it.",
        ]
        embed = discord.Embed(
            title="**My answer :**",
            description=f"{random.choice(answers)}",
            color=0xBEBEFE,
        )
        embed.set_footer(text=f"The question was : {question}")
        await context.send(embed=embed)

    @commands.hybrid_command(
        name="bitcoin",
        description="Get the current price of bitcoin.",
    )
    async def bitcoin(self, context: Context) -> None:
        """
        Obtenez le prix actuel du bitcoin.

        :param context: Le contexte de la commande hybride.
        """
        # Cela empêchera votre bot de tout arrêter lors d'une requête web - voir : https://discordpy.readthedocs.io/en/stable/faq.html#how-do-i-make-a-web-request
        async with aiohttp.ClientSession() as session:
            async with session.get(
                "https://api.coindesk.com/v1/bpi/currentprice/BTC.json"
            ) as request:
                if request.status == 200:
                    data = await request.json()
                    embed = discord.Embed(
                        title="Price of Bitcoin",
                        description=f"The current price is {data['bpi']['USD']['rate']} :dollar:",
                        color=0xBEBEFE,
                    )
                else:
                    embed = discord.Embed(
                        title="Error !",
                        description="There's a problem with the API, please try again later.",
                        color=0xE02B2B,
                    )
                await context.send(embed=embed)

    @app_commands.command(
        name="feedback", description="Submit feedback to bot owners"
    )
    async def feedback(self, interaction: discord.Interaction) -> None:
        """
        Soumettre un retour d'information aux propriétaires du bot.

        :param context: Le contexte de la commande hybride.
        """
        feedback_form = FeedbackForm()
        await interaction.response.send_modal(feedback_form)

        await feedback_form.wait()
        interaction = feedback_form.interaction
        await interaction.response.send_message(
            embed=discord.Embed(
                description="Thank you for your feedback, the owners have been informed.",
                color=0xBEBEFE,
            )
        )

        app_owner = (await self.bot.application_info()).owner
        await app_owner.send(
            embed=discord.Embed(
                title="Nouveau retour",
                description=f"{interaction.user} (<@{interaction.user.id}>) submitted a new return :\n{feedback_form.answer}"
            )
        )

async def setup(bot):
    await bot.add_cog(General(bot))