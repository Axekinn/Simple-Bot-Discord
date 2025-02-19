import discord
from discord.ext import commands
from discord import app_commands
from datetime import datetime, timezone
import platform

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
    return f"{days} days, {hours} hours, {minutes} minutes, {seconds} seconds"

def display_name_and_id(member):
    return f"{member.display_name} ({member.id})"

def get_member_status_emoji(member):
    status = str(member.status)
    return {
        'online': '🟢',
        'idle': '🟡',
        'dnd': '🔴',
        'offline': '⚫'
    }.get(status, '⚫')

def get_badges(user):
    badges = []
    flags = user.public_flags
    
    if user.bot:
        badges.append("🤖 Bot")
    if flags.staff:
        badges.append("👨‍💼 Discord Staff")
    if flags.partner:
        badges.append("🤝 Partner")
    # HypeSquad Houses
    if flags.hypesquad_bravery:
        badges.append("🏠 HypeSquad Bravery")
    if flags.hypesquad_brilliance:
        badges.append("🏠 HypeSquad Brilliance")
    if flags.hypesquad_balance:
        badges.append("🏠 HypeSquad Balance")
    if flags.hypesquad:
        badges.append("🎪 HypeSquad Events")
    if flags.bug_hunter:
        badges.append("🐛 Bug Hunter")
    if flags.bug_hunter_level_2:
        badges.append("🐛 Bug Hunter Level 2")
    if flags.early_supporter:
        badges.append("👑 Early Supporter")
    if flags.verified_bot_developer:
        badges.append("👨‍💻 Verified Bot Developer")
    if flags.active_developer:
        badges.append("👨‍💻 Active Developer")
    if flags.discord_certified_moderator:
        badges.append("🛡️ Certified Moderator")
    if flags.system:
        badges.append("⚙️ System")
    if flags.team_user:
        badges.append("👥 Team User")
    
    return badges if badges else ["No Badges"]

class Whois(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(
        name="whois",
        description="Get detailed information about a user"
    )
    @app_commands.describe(user="The user to get information about")
    async def whois(self, interaction: discord.Interaction, user: discord.User = None):
        try:
            target = user or interaction.user
            member = interaction.guild.get_member(target.id)

            embed = discord.Embed(
                color=member.color if member else discord.Color.blue()
            )
            
            # En-tête avec avatar
            embed.set_author(
                name=f"{target.name}#{target.discriminator}",
                icon_url=target.display_avatar.url
            )
            if target.banner:
                embed.set_image(url=target.banner.url)

            # Informations principales
            embed.add_field(
                name="📋 User Info",
                value=f"**ID:** {target.id}\n"
                      f"**Created:** <t:{int(target.created_at.timestamp())}:R>\n"
                      f"**Bot:** {'Yes' if target.bot else 'No'}\n",
                inline=False
            )

            # Badges
            badges = get_badges(target)
            if badges:
                embed.add_field(
                    name="🏅 Badges",
                    value="\n".join(badges),
                    inline=False
                )

            # Informations serveur (si membre)
            if member:
                status_emoji = get_member_status_emoji(member)
                roles = [role.mention for role in reversed(member.roles[1:])]
                
                embed.add_field(
                    name="🏠 Server Info",
                    value=f"**Nickname:** {member.nick or 'None'}\n"
                          f"**Status:** {status_emoji} {str(member.status).title()}\n"
                          f"**Joined:** <t:{int(member.joined_at.timestamp())}:R>\n"
                          f"**Boosting:** {'Since ' + f'<t:{int(member.premium_since.timestamp())}:R>' if member.premium_since else 'No'}\n",
                    inline=False
                )

                if roles:
                    embed.add_field(
                        name=f"👥 Roles [{len(roles)}]",
                        value=" ".join(roles[:10]) + ("..." if len(roles) > 10 else ""),
                        inline=False
                    )

                # Permissions clés
                key_perms = []
                if member.guild_permissions.administrator:
                    key_perms.append("Administrator")
                if member.guild_permissions.manage_guild:
                    key_perms.append("Manage Server")
                if member.guild_permissions.manage_roles:
                    key_perms.append("Manage Roles")
                if member.guild_permissions.manage_channels:
                    key_perms.append("Manage Channels")
                if member.guild_permissions.manage_messages:
                    key_perms.append("Manage Messages")
                if member.guild_permissions.kick_members:
                    key_perms.append("Kick Members")
                if member.guild_permissions.ban_members:
                    key_perms.append("Ban Members")

                if key_perms:
                    embed.add_field(
                        name="🔑 Key Permissions",
                        value=", ".join(key_perms),
                        inline=False
                    )
            else:
                embed.set_footer(text="⚠️ This user is not on this server")

            await interaction.response.send_message(embed=embed)

        except Exception as e:
            print(f"Error in whois command: {str(e)}")
            await interaction.response.send_message(
                "❌ An error occurred while fetching user information.",
                ephemeral=True
            )

async def setup(bot):
    await bot.add_cog(Whois(bot))