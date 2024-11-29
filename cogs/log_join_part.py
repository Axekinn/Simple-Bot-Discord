import discord
from discord.ext import commands
from discord.utils import escape_markdown

from ext import functions


class JoinPart(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        log_type = {
            'type': 'rejoin' if member.flags.did_rejoin else 'join',
            'channel_id': 1251225103702687774,  # Remplacez par l'ID du salon de logs
            'message_format': 'extended',
            'label': 'join',
            'icon': '🟢'  # Ajoutez l'icône appropriée
        }
        if not functions.enabled_check(bot=self.bot, guild_id=member.guild.id, log_type=log_type['type']):
            return

        message, footer = await self.guild_invite_compare(member.guild)
        await self.log_join_part(log_type=log_type, member=member, message=message, footer=footer)

        channel = self.bot.get_channel(log_type['channel_id'])
        if channel:
            embed = discord.Embed(
                title="Membre a rejoint",
                description=f"{member.mention} a rejoint le serveur.",
                color=discord.Color.green()
            )
            if member.avatar:
                embed.set_thumbnail(url=member.avatar.url)
            embed.add_field(name="Nom d'utilisateur", value=member.name, inline=True)
            embed.add_field(name="ID de l'utilisateur", value=member.id, inline=True)
            embed.add_field(name="Compte créé le", value=member.created_at.strftime("%d %B %Y à %H:%M"), inline=True)
            await channel.send(embed=embed)

    @commands.Cog.listener()
    async def on_raw_member_remove(self, payload: discord.RawMemberRemoveEvent):
        log_type = {
            'type': 'part',
            'channel_id': 1251225103702687774,  # Remplacez par l'ID du salon de logs
            'message_format': 'extended',
            'label': 'part',
            'icon': '🔴'  # Ajoutez l'icône appropriée
        }
        if not functions.enabled_check(bot=self.bot, guild_id=payload.guild_id, log_type=log_type['type']):
            return

        guild = self.bot.get_guild(payload.guild_id)
        user = payload.user

        if user:
            await self.log_join_part(log_type=log_type, member=user)

    @commands.Cog.listener()
    async def on_invite_create(self, invite: discord.Invite):
        await functions.set_guild_invites(bot=self.bot, guild=invite.guild)

    @commands.Cog.listener()
    async def on_invite_delete(self, invite: discord.Invite):
        await functions.set_guild_invites(bot=self.bot, guild=invite.guild)

    async def log_join_part(self, log_type: dict, member: discord.Member, message: str = None, footer: str = None):
        channel = self.bot.get_channel(log_type['channel_id'])
        if channel:
            await functions.log_event(
                bot=self.bot,
                log_type=log_type,
                user=member,
                message=message,
                footer=footer,
                moderator=None
            )
        else:
            print(f"Channel with ID '{log_type['channel_id']}' not found in guild '{member.guild.name}'")

    async def guild_invite_compare(self, guild: discord.Guild):
        message, footer = None, None
        before_invites = self.bot.guild_settings[guild.id].get('invites', [])
        before_dict = {invite.code: invite.uses for invite in before_invites}

        try:
            after_invites = await guild.invites()
        except discord.Forbidden:
            after_invites = []

        if after_invites:
            self.bot.guild_settings[guild.id]['invites'] = after_invites

            for after in after_invites:
                before_uses = before_dict.get(after.code)
                if before_uses is not None and before_uses < after.uses:
                    message = f'Invited by: {after.inviter.mention} `{after.inviter}`'
                    footer = f'Invite: {after.code}'
                    break

        return message, footer

    @commands.Cog.listener()
    async def on_member_remove(self, member: discord.Member):
        channel = self.bot.get_channel(1251225103702687774)  # Remplacez par l'ID du salon de logs
        if channel:
            embed = discord.Embed(
                title="Membre a quitté",
                description=f"{member.mention} a quitté le serveur.",
                color=discord.Color.red()
            )
            if member.avatar:
                embed.set_thumbnail(url=member.avatar.url)
            embed.add_field(name="Nom d'utilisateur", value=member.name, inline=True)
            embed.add_field(name="ID de l'utilisateur", value=member.id, inline=True)
            embed.add_field(name="Rejoint le", value=member.joined_at.strftime("%d %B %Y à %H:%M"), inline=True)
            await channel.send(embed=embed)


class LogJoinPart(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        channel = self.bot.get_channel(1251225103702687774)  # Replace with the log channel ID
        if channel:
            embed = discord.Embed(
                title="Nouveau membre",
                description=f"{member.mention} a rejoint le serveur.",
                color=discord.Color.green()
            )
            if member.avatar:
                embed.set_thumbnail(url=member.avatar.url)
            embed.add_field(name="Nom d'utilisateur", value=member.name, inline=True)
            embed.add_field(name="ID de l'utilisateur", value=member.id, inline=True)
            embed.add_field(name="Rejoint le", value=member.joined_at.strftime("%d %B %Y à %H:%M"), inline=True)
            await channel.send(embed=embed)

    @commands.Cog.listener()
    async def on_member_remove(self, member: discord.Member):
        channel = self.bot.get_channel(1251225103702687774)  # Replace with the log channel ID
        if channel:
            embed = discord.Embed(
                title="Membre a quitté",
                description=f"{member.mention} a quitté le serveur.",
                color=discord.Color.red()
            )
            if member.avatar:
                embed.set_thumbnail(url=member.avatar.url)
            embed.add_field(name="Nom d'utilisateur", value=member.name, inline=True)
            embed.add_field(name="ID de l'utilisateur", value=member.id, inline=True)
            embed.add_field(name="Rejoint le", value=member.joined_at.strftime("%d %B %Y à %H:%M"), inline=True)
            await channel.send(embed=embed)

class LogMemberActions(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_user_update(self, before: discord.User, after: discord.User):
        log_type = 'username'

        for guild in after.mutual_guilds:
            try:
                if not functions.enabled_check(bot=self.bot, guild_id=guild.id, log_type=log_type):
                    continue

                message = f'from **{escape_markdown(str(before))}** to **{escape_markdown(str(after))}**'
                if str(before) != str(after):
                    await self.log_member_update_event(log_type=log_type, member=after, message=message, guild=guild)
            except Exception as e:
                print(f"Error in on_user_update: {e}")

    @commands.Cog.listener()
    async def on_member_update(self, before: discord.Member, after: discord.Member):
        update_checks = {
            (before.nick, after.nick): lambda: self.nick_handler(before, after),
            (before.pending, after.pending): lambda: self.log_member_update_event(
                log_type='pending',
                member=after,
                message='verified',
                guild=after.guild
            ),
            (before.flags.started_onboarding, after.flags.started_onboarding): lambda: self.log_member_update_event(
                log_type='onboarding',
                member=after,
                message='started',
                guild=after.guild
            ),
            (before.flags.completed_onboarding, after.flags.completed_onboarding): lambda: self.log_member_update_event(
                log_type='onboarding',
                member=after,
                message='completed',
                guild=after.guild
            )
        }

        for (before_attr, after_attr), handler in update_checks.items():
            try:
                if before_attr != after_attr:
                    await handler()
                    break
            except Exception as e:
                print(f"Error in on_member_update: {e}")

    async def nick_handler(self, before: discord.Member, after: discord.Member):
        log_type = 'nick'
        try:
            if not functions.enabled_check(bot=self.bot, guild_id=after.guild.id, log_type=log_type):
                return

            nick_changes = {
                (False, True): lambda: self.log_member_update_event(
                    log_type=log_type,
                    member=after,
                    message=f'set nick to **{escape_markdown(after.nick)}**',
                    guild=after.guild
                ),
                (True, False): lambda: self.log_member_update_event(
                    log_type=log_type,
                    member=before,
                    message=f'removed nickname **{escape_markdown(before.nick)}**',
                    guild=before.guild
                ),
                (True, True): lambda: self.log_member_update_event(
                    log_type=log_type,
                    member=after,
                    message=f'changed nickname from **{escape_markdown(before.nick)}** to **{escape_markdown(after.nick)}**',
                    guild=after.guild
                )
            }

            for (before_nick, after_nick), handler in nick_changes.items():
                if (before_nick is not None) != (after_nick is not None):
                    await handler()
        except Exception as e:
            print(f"Error in nick_handler: {e}")

    async def log_member_update_event(self, log_type: str, member: discord.Member, message: str, guild: discord.Guild):
        try:
            # Your logging logic here
            pass
        except Exception as e:
            print(f"Error in log_member_update_event: {e}")

async def setup(bot: commands.Bot):
    await bot.add_cog(JoinPart(bot))
    await bot.add_cog(LogMemberActions(bot))
    await bot.add_cog(LogJoinPart(bot))