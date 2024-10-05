from __future__ import annotations

import discord
from discord.ui import Modal, View, TextInput, button
from typing import TYPE_CHECKING, Dict, List
import re
import os
from dotenv import load_dotenv

if TYPE_CHECKING:
    from utils.context import Context
    from .verify import Verification
    from bot import UniversityBot


load_dotenv()
UNIVERSITY_EMAIL_SUFFIX = os.getenv("UNIVERSITY_EMAIL_SUFFIX")
EMAIL_RE = rf"\d+@{re.escape(UNIVERSITY_EMAIL_SUFFIX)}"
try:
    ROLES_ON_VERIFICTION: List[int] = [int(v) for v in os.getenv("ROLES_ON_VERIFICATION").split(",")]
except AttributeError:
    ROLES_ON_VERIFICTION = []


class SetEmailModal(Modal, title="Edit Email Address"):
    def __init__(self, view: VerifyView):
        super().__init__()
        self.view: VerifyView = view
        self.email: TextInput = TextInput(
            label="University Email Address",
            default=self.view.email,
            placeholder="xyz@email.com",
            min_length=10,
            max_length=50
        )
        self.add_item(self.email)

    async def on_submit(self, interaction: discord.Interaction) -> None:
        if not re.fullmatch(EMAIL_RE, self.email.value):
            await interaction.response.send_message("Invalid Email!", ephemeral=True)
            return
        found = await self.bot.db.verification.find({"email": self.email.value})
        if found:
            # email is already been used to verify another person
            await interaction.response.send_message("This email has already been used to verify another party!", ephemeral=True)
            return
        self.view.email = self.email.value
        await interaction.response.send_message("Email Set!", ephemeral=True)


class VerifyModal(Modal, title="OTP"):
    def __init__(self, view: VerifyView):
        super().__init__()
        self.view: VerifyView = view
        self.otp_code: TextInput = TextInput(
            label="OTP Code",
            placeholder="The one time password sent to your email!",
            min_length=1,
            max_length=12
        )
        self.add_item(self.otp_code)

    async def on_submit(self, interaction: discord.Interaction) -> None:
        length = len(self.otp_code.value)
        if length != 9:
            await interaction.response.send_message("Invalid OTP!", ephemeral=True)
            return

        otp_code = self.view.cog.get_otp(interaction.user.id)
        if not otp_code:
            await interaction.response.send_message("OTP code has expired", ephemeral=True)
            return

        if otp_code['code'] != self.otp_code.value:
            await interaction.response.send_message("Invalid OTP!", ephemeral=True)
            return

        await interaction.response.defer()

        data = {
            "_id": interaction.user.id,
            "email": self.view.email,
        }

        await self.view.ctx.bot.db.verification.insert(
            data
        )

        self.view.stop()
        if ROLES_ON_VERIFICTION:
            roles = [v for v in [interaction.guild.get_role(r) for r in ROLES_ON_VERIFICTION] if v]
            await interaction.user.add_roles(*roles, atomic=False, reason="Passed Verification")
        await interaction.followup.send("You are now verified!", ephemeral=True)


class VerifyView(View):
    def __init__(self, ctx: Context, cog: Verification):
        super().__init__(timeout=480)
        self.ctx: Context = ctx
        self.cog: Verification = cog
        self.email = None

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id == self.ctx.author.id:
            return True
        await interaction.response.send_message("This is not for you", ephemeral=True)
        return False

    @button(label="Email", style=discord.ButtonStyle.blurple)
    async def email(self, interaction: discord.Interaction, btn: discord.Button) -> None:
        await interaction.response.send_modal(SetEmailModal(self))

    @button(label="Send OTP", style=discord.ButtonStyle.red)
    async def send_register_code(self, interaction: discord.Interaction, btn: discord.Button) -> None:
        if not self.email:
            await interaction.response.send_message(
                "You need to set an email!", ephemeral=True
            )
            return
        await interaction.response.defer(ephemeral=True)
        otp = self.cog.get_otp(interaction.user.id)
        if otp:
            await interaction.followup.send(
                f"OTP was already sent and expires {discord.utils.format_dt(otp['expires'], 'R')}",
                ephemeral=True
            )
            return
        otp_code = self.cog.generate_otp(interaction.user.id)
        result = await self.ctx.bot.email.send_email(
            self.email,
            "Discord Verification",
            f"Hello,\n\nYour one time password is: {otp_code['code']}"
        )
        if result:
            await interaction.followup.send("An otp code has been sent to your email!\nMake sure to check your junk folder!", ephemeral=True)
        else:
            await interaction.followup.send(
                "The email service seems to be down!\nTry again later.",
                ephemeral=True
            )

    @button(label="Verify", style=discord.ButtonStyle.green)
    async def register(self, interaction: discord.Interaction, btn: discord.Button) -> None:
        if not self.email:
            await interaction.response.send_message(
                "You need to set an email!", ephemeral=True
            )
            return
        await interaction.response.send_modal(VerifyModal(self))