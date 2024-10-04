from __future__ import annotations

import discord
from discord.ext import commands
from typing import TYPE_CHECKING, TypedDict, AnyStr, Dict, Never, Optional
from datetime import datetime, timedelta
import string
import random
import asyncio
from .views import VerifyView


if TYPE_CHECKING:
    from bot import UniversityBot
    from cogs.email import Email
    from utils.context import Context


class OTPCache(TypedDict):
    code: str
    expires: datetime  # 5 minutes


class Verification(commands.Cog):
    def __init__(self, bot: UniversityBot) -> None:
        self.bot: UniversityBot = bot
        self.__verify_otp: Dict[int, OTPCache] = {}
        self.__otp_length: int = 9
        self.__otp_expires_minutes: int = 5
        self.__request_expires_minutes: int = 15
        self.__printable: AnyStr = ''.join([string.ascii_letters, string.digits])  # optional: string.punctuation 
    
    def generate_otp(self, user_id: int) -> OTPCache:
        if user_id in self.__verify_otp:
            return self.get_otp(user_id)
        otp_code = ''.join(random.SystemRandom().choices(self.__printable, k=self.__otp_length))
        data: OTPCache = {
                'code': otp_code,
                'expires': discord.utils.utcnow() + timedelta(minutes=self.__otp_expires_minutes)
            }

        self.__verify_otp[user_id] = data
        return data

    def get_otp(self, user_id: int) -> Optional[OTPCache]:
        result = self.__verify_otp.get(user_id)
        if result:
            if result['expires'] <= discord.utils.utcnow():
                del self.__verify_otp[user_id]
                return
            return result
        return


    async def clear_cache(self) -> Never:
        while True:

            for user, otp in self.__verify_otp.copy().items():
                if otp['expires'] < discord.utils.utcnow():
                    del self.__verify_otp[user]

            await asyncio.sleep(60)
    

    @commands.hybrid_command(name="verify")
    async def verify(self, ctx: Context) -> None:
        """ Verify your account as a genuine student."""
        if ctx.interaction:
            await ctx.defer(ephemeral=True)
        else:
            await ctx.typing()
        # check if user has verified!
        found = await self.bot.db.verification.find({"_id": ctx.author.id})
        if found:
            await ctx.reply(
                "Your account is already verified",
                ephemeral=True
            )
            return

        view = VerifyView(ctx, self)
        await ctx.reply(
            "Verify your account by clicking the button below!",
            view=view,
            ephemeral=True
        )
  