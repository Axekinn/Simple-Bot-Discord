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
        super().__init__(title="Retour d'information")
    feedback = discord.ui.TextInput(
        label="Que pensez-vous de ce bot ?",
        style=discord.TextStyle.long,
        placeholder="Tapez votre réponse ici...",
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
            name="Obtenir l'ID", callback=self.grab_id
        )
        self.bot.tree.add_command(self.context_menu_user)
        self.context_menu_message = app_commands.ContextMenu(
            name="Supprimer les spoilers", callback=self.remove_spoilers
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
            title="Message sans spoilers",
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
            description=f"L'ID de {user.mention} est `{user.id}`.",
            color=0xBEBEFE,
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @commands.hybrid_command(name="help", description="Affiche la liste des commandes disponibles.")
    async def help(self, ctx):
        """
        Affiche la liste des commandes disponibles.

        :param ctx: Le contexte de la commande.
        """
        embed = discord.Embed(title="Aide", description="Voici la liste des commandes disponibles :", color=0x00ff00)
        for cog_name, cog in self.bot.cogs.items():
            if cog is not None:
                commands_list = ""
                for command in cog.get_commands():
                    command_name = command.name
                    command_description = command.description if command.description else "Pas de description."
                    commands_list += f"**/{command_name}** - {command_description}\n"
                if commands_list:
                    embed.add_field(name=cog_name.capitalize(), value=commands_list, inline=False)
        await ctx.send(embed=embed)

    @commands.hybrid_command(name="botinfo", description="Obtenir des informations utiles (ou non) sur le bot.")
    async def botinfo(self, context: commands.Context) -> None:
        """
        Obtenir des informations utiles (ou non) sur le bot.

        :param context: Le contexte de la commande hybride.
        """
        embed = discord.Embed(
            description="Utilisation du modèle [Krypton](https://krypton.ninja)",
            color=0xBEBEFE,
        )
        embed.set_author(name="Informations sur le bot")
        embed.add_field(name="Propriétaire:", value="_axekin", inline=True)
        embed.add_field(
            name="Version de Python:", value=f"{platform.python_version()}", inline=True
        )
        embed.add_field(
            name="Préfixe:",
            value=f"/ (Commandes Slash) ou {self.bot.command_prefix} pour les commandes normales",
            inline=False,
        )
        embed.set_footer(text=f"Demandé par {context.author}")
        await context.send(embed=embed)

    @commands.hybrid_command(
        name="serverinfo",
        description="Obtenir des informations utiles (ou non) sur le serveur.",
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
            roles.append(f">>>> Affichage de [50/{num_roles}] rôles")
        await context.send(embed=discord.Embed(title="Informations sur le serveur", description="\n".join(roles), color=0x00ff00))

    @commands.hybrid_command(
        name="ping",
        description="Vérifier si le bot est vivant.",
    )
    async def ping(self, context: Context) -> None:
        """
        Vérifier si le bot est vivant.

        :param context: Le contexte de la commande hybride.
        """
        embed = discord.Embed(
            title="🏓 Pong!",
            description=f"Le temps de latence du bot est de {round(self.bot.latency * 1000)}ms.",
            color=0xBEBEFE,
        )
        await context.send(embed=embed)

    @commands.hybrid_command(
        name="invite",
        description="Obtenir le lien d'invitation du bot pour pouvoir l'inviter.",
    )
    async def invite(self, context: Context) -> None:
        """
        Obtenir le lien d'invitation du bot pour pouvoir l'inviter.

        :param context: Le contexte de la commande hybride.
        """
        embed = discord.Embed(
            description=f"Invitez-moi en cliquant [ici]({self.bot.config['invite_link']}).",
            color=0xD75BF4,
        )
        try:
            await context.author.send(embed=embed)
            await context.send("Je vous ai envoyé un message privé !")
        except discord.Forbidden:
            await context.send(embed=embed)

    @commands.hybrid_command(
        name="server",
        description="Obtenez le lien d'invitation du serveur discord du bot pour obtenir de l'aide.",
    )
    async def server(self, context: Context) -> None:
        """
        Obtenez le lien d'invitation du serveur discord du bot pour obtenir de l'aide.

        :param context: Le contexte de la commande hybride.
        """
        embed = discord.Embed(
            description=f"Rejoignez le serveur de support pour le bot en cliquant [ici](https://discord.com/invite/emulationfr).",
            color=0xD75BF4,
        )
        try:
            await context.author.send(embed=embed)
            await context.send("Je vous ai envoyé un message privé !")
        except discord.Forbidden:
            await context.send(embed=embed)

    @commands.hybrid_command(
        name="8ball",
        description="Posez n'importe quelle question au robot.",
    )
    @app_commands.describe(question="La question que vous voulez poser.")
    async def eight_ball(self, context: Context, *, question: str) -> None:
        """
        Posez n'importe quelle question au robot.

        :param context: Le contexte de la commande hybride.
        :param question: La question que vous voulez poser.
        """
        answers = [
            "C'est certain.",
            "Sans aucun doute.",
            "Vous pouvez compter dessus.",
            "Oui - définitivement.",
            "Très probable.",
            "Les perspectives sont bonnes.",
            "Oui.",
            "Les signes indiquent que oui.",
            "Réponse floue, réessayez.",
            "Demandez plus tard.",
            "Mieux vaut ne pas vous le dire maintenant.",
            "Impossible de prédire maintenant.",
            "Concentrez-vous et demandez à nouveau.",
            "Ne comptez pas dessus.",
            "Ma réponse est non.",
            "Mes sources disent non.",
            "Les perspectives ne sont pas si bonnes.",
            "Très douteux.",
            "Absolument.",
            "Je ne pense pas.",
            "C'est possible.",
            "Je ne peux pas le dire maintenant.",
            "C'est une certitude.",
            "Je ne suis pas sûr.",
            "Oui, mais avec des réserves.",
            "Non, pas du tout.",
            "Les chances sont faibles.",
            "Les chances sont élevées.",
            "Je dirais oui.",
            "Je dirais non.",
            "Peut-être.",
            "Probablement pas.",
            "Probablement oui.",
            "Les signes sont flous.",
            "Les signes sont clairs.",
            "Je ne peux pas répondre maintenant.",
            "Essayez encore.",
            "Demandez à nouveau plus tard.",
            "Je ne sais pas.",
            "Je ne peux pas prédire cela.",
        ]
        embed = discord.Embed(
            title="**Ma réponse :**",
            description=f"{random.choice(answers)}",
            color=0xBEBEFE,
        )
        embed.set_footer(text=f"La question était : {question}")
        await context.send(embed=embed)

    @commands.hybrid_command(
        name="bitcoin",
        description="Obtenez le prix actuel du bitcoin.",
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
                        title="Prix du Bitcoin",
                        description=f"Le prix actuel est de {data['bpi']['USD']['rate']} :dollar:",
                        color=0xBEBEFE,
                    )
                else:
                    embed = discord.Embed(
                        title="Erreur !",
                        description="Il y a un problème avec l'API, veuillez réessayer plus tard.",
                        color=0xE02B2B,
                    )
                await context.send(embed=embed)

    @app_commands.command(
        name="feedback", description="Soumettre un retour d'information aux propriétaires du bot"
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
                description="Merci pour votre retour, les propriétaires ont été informés.",
                color=0xBEBEFE,
            )
        )

        app_owner = (await self.bot.application_info()).owner
        await app_owner.send(
            embed=discord.Embed(
                title="Nouveau retour",
                description=f"{interaction.user} (<@{interaction.user.id}>) a soumis un nouveau retour :\n{feedback_form.answer}"
            )
        )

async def setup(bot):
    await bot.add_cog(General(bot))