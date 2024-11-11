from bot import UniversityBot

from .reminder import Reminder, Timer

__all__ = ["Reminder", "Timer"]


async def setup(bot: UniversityBot):
    await bot.add_cog(Reminder(bot))
