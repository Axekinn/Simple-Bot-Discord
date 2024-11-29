import discord
from discord.ext import commands
from discord.utils import escape_markdown

from ext import functions


class LogMemberActions(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_user_update(self, before: discord.User, after: discord.User):
        log_type = 'username'

        for guild in after.mutual_guilds:
            if not functions.enabled_check(bot=self.bot, guild_id=guild.id, log_type=log_type):
                continue

            if str(before) != str(after):
                message = f'from **{escape_markdown(str(before))}** to **{escape_markdown(str(after))}**'
                await self.log_member_update_event(log_type=log_type, member=after, message=message, guild=guild)

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

    async def log_member_update_event(self, log_type: str, member: discord.Member, message: str, guild: discord.Guild):
        # Log the member update event
        pass

    async def nick_handler(self, before: discord.Member, after: discord.Member):
        log_type = 'nick'
        try:
            if not functions.enabled_check(bot=self.bot, guild_id=after.guild.id, log_type=log_type):
                return

            nick_changes = {
                (before.nick is None, after.nick is not None): lambda: self.log_member_update_event(
                    log_type=log_type,
                    member=after,
                    message=f'set nick to **{escape_markdown(after.nick)}**',
                    guild=after.guild
                ),
                (before.nick is not None, after.nick is None): lambda: self.log_member_update_event(
                    log_type=log_type,
                    member=before,
                    message=f'removed nickname **{escape_markdown(before.nick)}**',
                    guild=before.guild
                ),
                (before.nick is not None, after.nick is not None): lambda: self.log_member_update_event(
                    log_type=log_type,
                    member=after,
                    message=f'changed nickname from **{escape_markdown(before.nick)}** to **{escape_markdown(after.nick)}**',
                    guild=after.guild
                )
            }

            for (before_nick, after_nick), handler in nick_changes.items():
                if before_nick != after_nick:
                    await handler()
                    break
        except Exception as e:
            print(f"Error in nick_handler: {e}")

async def setup(bot: commands.Bot):
    if bot.get_cog('LogMemberActions') is None:
        await bot.add_cog(LogMemberActions(bot))
