from __future__ import annotations

from discord.ext import commands
import aiosmtplib
from typing import TYPE_CHECKING, Optional
from email.mime.text import MIMEText
from dotenv import load_dotenv
import os
import logging 

if TYPE_CHECKING:
    from bot import UniversityBot

load_dotenv()
log = logging.getLogger(__name__)


class Email(commands.Cog):
    def __init__(self, bot: UniversityBot):
        self.bot: UniversityBot = bot
        self.__sender_email: str = os.getenv('EMAIL_ADDRESS')
        self.__sender_password: str = os.getenv('EMAIL_APP_PASSWORD')
        self.__smtp_client: Optional[aiosmtplib.SMTP] = None
    
    async def cog_load(self) -> None:
        self.__smtp_client = aiosmtplib.SMTP(
            hostname='smtp.gmail.com',
            port=587,
            start_tls=True
        )
        await self.__smtp_client.connect()
        await self.__smtp_client.login(self.__sender_email, self.__sender_password)

    async def cog_unload(self) -> None:
        if self.__smtp_client and self.__smtp_client.is_connected():
            await self.__smtp_client.quit()

    async def send_email(
        self,
        email: str,
        subject: str,
        body: str,
        ) -> bool:
        """Sends the OTP code to the provided email address using Gmail's SMTP server."""
        if not self.__smtp_client:
            return False

        message = MIMEText(body)
        message['Subject'] = subject
        message['From'] = self.__sender_email
        message['To'] = email

        try:
            if not self.__smtp_client.is_connected:
                if self.__smtp_client._connect_lock and self.__smtp_client._connect_lock.locked():
                    self.__smtp_client.close()
                log.warning("smtp client closed")
                await self.__smtp_client.connect()
                log.info("smtp client connected")
            await self.__smtp_client.send_message(message)
        except aiosmtplib.SMTPException as e:
            if not self.__smtp_client.is_connected:
                if self.__smtp_client._connect_lock and self.__smtp_client._connect_lock.locked():
                    self.__smtp_client.close()
                log.warning("with exception: smtp client closed")
                await self.__smtp_client.connect()
                log.info("with exception: smtp client connected")
            await self.__smtp_client.login(self.__sender_email, self.__sender_password)
            log.info("with exception: smtp client logged in")

            # Retry sending the email
            try:
                await self.__smtp_client.send_message(message)
            except Exception:
                return False
        return True

        