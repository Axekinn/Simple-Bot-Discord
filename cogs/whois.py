import discord
from discord.ext import commands
from datetime import datetime, timezone

intents = discord.Intents.default()
intents.members = True  # Nécessaire pour accéder aux informations des membres

bot = commands.Bot(command_prefix='!', intents=intents)

def convert_date_for_discord(date):
    return date.strftime("%d %B %Y %H:%M")

def diff_date(date):
    # Convertir la date en UTC aware
    now = datetime.now(timezone.utc)
    # S'assurer que la date d'entrée est aussi en UTC
    if date.tzinfo is None:
        date = date.replace(tzinfo=timezone.utc)
    delta = now - date
    days = delta.days
    hours, remainder = divmod(delta.seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    return f"{days} jours, {hours} heures"

def display_name_and_id(member):
    return f"{member.display_name} ({member.id})"

class Whois(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name='whois')
    async def whois(self, ctx, member: discord.Member = None):
        if member is None:
            member = ctx.author

        embed = discord.Embed(color=member.color)
        embed.set_author(
            name=display_name_and_id(member),
            icon_url=member.avatar.url if member.avatar else None
        )
        embed.add_field(
            name="Compte de l'utilisateur",
            value=member,
            inline=True
        )
        embed.add_field(
            name='Compte créé le',
            value=convert_date_for_discord(member.created_at),
            inline=True
        )
        embed.add_field(
            name="Âge du compte",
            value=diff_date(member.created_at),
            inline=True
        )
        embed.add_field(
            name='Mention',
            value=member.mention,
            inline=True
        )
        embed.add_field(
            name='Serveur rejoint le',
            value=convert_date_for_discord(member.joined_at),
            inline=True
        )
        embed.add_field(
            name='Est sur le serveur depuis',
            value=diff_date(member.joined_at),
            inline=True
        )

        if member.premium_since:
            embed.add_field(
                name='Boost Nitro depuis',
                value=diff_date(member.premium_since),
                inline=True
            )
            
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(Whois(bot))