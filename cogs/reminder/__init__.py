from .reminder import Reminder, Timer
from bot import UniversityBot

__all__ = ['Reminder', 'Timer']


async def setup(bot: UniversityBot):
    await bot.add_cog(Reminder(bot))