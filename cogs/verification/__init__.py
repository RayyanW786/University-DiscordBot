from __future__ import annotations

from typing import TYPE_CHECKING

from .verify import Verification

if TYPE_CHECKING:
    from bot import UniversityBot

__all__ = ["Verification"]


async def setup(bot: UniversityBot):
    await bot.add_cog(Verification(bot))
