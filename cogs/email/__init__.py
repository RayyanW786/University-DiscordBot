from __future__ import annotations

from .email import Email
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from bot import UniversityBot

__all__ = ['Email']


async def setup(bot: UniversityBot):
    await bot.add_cog(Email(bot))