from __future__ import annotations

import asyncio
import os
import random
import string
from datetime import datetime, timedelta
from typing import TYPE_CHECKING, AnyStr, Dict, List, Never, Optional, TypedDict

import discord
from discord.ext import commands

from .views import VerifyView

if TYPE_CHECKING:
    from bot import UniversityBot
    from utils.context import Context


class OTPCache(TypedDict):
    code: str
    expires: datetime  # 5 minutes


try:
    ROLES_ON_VERIFICATION: List[int] = [
        int(v) for v in os.getenv("ROLES_ON_VERIFICATION").split(",")
    ]
except AttributeError:
    ROLES_ON_VERIFiCATION = []


class Verification(commands.Cog):
    def __init__(self, bot: UniversityBot) -> None:
        self.bot: UniversityBot = bot
        self.__verify_otp: Dict[int, OTPCache] = {}
        self.__otp_length: int = 9
        self.__otp_expires_minutes: int = 5
        self.__request_expires_minutes: int = 15
        self.__printable: AnyStr = "".join(
            [string.ascii_letters, string.digits]
        )  # optional: string.punctuation

    def generate_otp(self, user_id: int) -> OTPCache:
        if user_id in self.__verify_otp:
            return self.get_otp(user_id)
        otp_code = "".join(
            random.SystemRandom().choices(self.__printable, k=self.__otp_length)
        )
        data: OTPCache = {
            "code": otp_code,
            "expires": discord.utils.utcnow()
            + timedelta(minutes=self.__otp_expires_minutes),
        }

        self.__verify_otp[user_id] = data
        return data

    def get_otp(self, user_id: int) -> Optional[OTPCache]:
        result = self.__verify_otp.get(user_id)
        if result:
            if result["expires"] <= discord.utils.utcnow():
                del self.__verify_otp[user_id]
                return
            return result
        return

    async def clear_cache(self) -> Never:
        while True:
            for user, otp in self.__verify_otp.copy().items():
                if otp["expires"] < discord.utils.utcnow():
                    del self.__verify_otp[user]

            await asyncio.sleep(60)

    @commands.hybrid_command(name="verify")
    async def verify(self, ctx: Context) -> None:
        """Verify your account as a genuine student."""
        if ctx.interaction:
            await ctx.defer(ephemeral=True)
        else:
            await ctx.typing()
        # check if user has verified!
        found = await self.bot.db.verification.find({"_id": ctx.author.id})
        if found:
            # check if user has the verified role
            if ROLES_ON_VERIFICATION:
                auth_roles = [r.id for r in ctx.author.roles]
                for role in ROLES_ON_VERIFICATION:
                    if role not in auth_roles:
                        break
            else:
                await ctx.reply("Your account is already verified", ephemeral=True)
                return

            roles = [
                v for v in [ctx.guild.get_role(r) for r in ROLES_ON_VERIFICATION] if v
            ]
            await ctx.author.add_roles(
                *roles, atomic=False, reason="Passed Verification"
            )
            await ctx.reply(
                "Your account now has the verified"
                + (" role!" if len(roles) == 1 else " roles!"),
                ephemeral=True,
            )
            return

        view = VerifyView(ctx, self)
        await ctx.reply(
            "Verify your account by clicking the button below!",
            view=view,
            ephemeral=True,
        )
