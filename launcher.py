from __future__ import annotations

import os
import logging
import asyncio
import discord
import contextlib
from logging.handlers import RotatingFileHandler
from dotenv import load_dotenv
from bot import UniversityBot

try:
    import uvloop  # type: ignore
except ImportError:
    pass
else:
    ev_policy = asyncio.WindowsProactorEventLoopPolicy() if os.name == "nt" else uvloop.EventLoopPolicy
    asyncio.set_event_loop_policy(policy=ev_policy)

load_dotenv()

os.environ["JISHAKU_NO_UNDERSCORE"] = "True"
os.environ["JISHAKU_NO_DM_TRACEBACK"] = "True"
os.environ["JISHAKU_HIDE"] = "True"


class RemoveNoise(logging.Filter):
    def __init__(self):
        super().__init__(name='discord.state')

    def filter(self, record: logging.LogRecord) -> bool:
        if record.levelname == 'WARNING' and 'referencing an unknown' in record.msg:
            return False
        return True


@contextlib.contextmanager
def setup_logging():
    log = logging.getLogger()

    try:
        discord.utils.setup_logging()
        # __enter__
        max_bytes = 32 * 1024 * 1024  # 32 MiB
        logging.getLogger('discord').setLevel(logging.INFO)
        logging.getLogger('discord.http').setLevel(logging.WARNING)
        logging.getLogger('discord.state').addFilter(RemoveNoise())

        log.setLevel(logging.INFO)
        handler = RotatingFileHandler(
            filename='logs/console.log',
            encoding='utf-8',
            mode='w',
            maxBytes=max_bytes,
            backupCount=5
        )
        dt_fmt = '%Y-%m-%d %H:%M:%S'
        fmt = logging.Formatter('[{asctime}] [{levelname:<7}] {name}: {message}', dt_fmt, style='{')
        handler.setFormatter(fmt)
        log.addHandler(handler)

        yield

    finally:
        # __exit__
        handlers = log.handlers[:]
        for hdlr in handlers:
            hdlr.close()
            log.removeHandler(hdlr)


async def run_bot():
    async with UniversityBot() as bot:
        await bot.start()


if __name__ == "__main__":
    with setup_logging():
        asyncio.run(run_bot())