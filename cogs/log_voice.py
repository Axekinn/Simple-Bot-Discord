import discord
from discord.ext import commands

from ext import functions


class LogVoice(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_voice_state_update(self, member: discord.Member, before: discord.VoiceState, after: discord.VoiceState):
        log_type = 'voice_state_update'
        message = f'{member} changed voice state.'

        try:
            await self.log_voice_event(log_type=log_type, member=member, message=message)
        except Exception as e:
            print(f"Error in on_voice_state_update: {e}")

    async def log_voice_event(self, log_type, member, message):
        try:
            await functions.log_event(
                channel=member.guild.system_channel,
                content=message,
                embed_data={
                    'author': {
                        'name': member.name,
                        'icon_url': str(member.avatar_url)
                    },
                    'footer': log_type
                }
            )
        except Exception as e:
            print(f"Error in log_voice_event: {e}")

async def setup(bot: commands.Bot):
    await bot.add_cog(LogVoice(bot))
