from __future__ import annotations

import io
from typing import (
    TYPE_CHECKING,
    Any,
    Callable,
    Generic,
    Iterable,
    Optional,
    Sequence,
    TypeVar,
    Union,
)

import aiohttp
import discord
from discord.ext import commands

if TYPE_CHECKING:
    from bot import UniversityBot

T = TypeVar("T")

__all__ = ["ConfirmationView", "DisambiguatorView", "Context", "GuildContext"]


class ConfirmationView(discord.ui.View):
    def __init__(
        self,
        *,
        timeout: float,
        author_id: int,
        delete_after: bool,
        confirm_label: str,
        cancel_label: str,
    ) -> None:
        super().__init__(timeout=timeout)
        self.value: Optional[bool] = None
        self.delete_after: bool = delete_after
        self.author_id: int = author_id
        self.message: Optional[discord.Message] = None
        self.confirm.label = confirm_label
        self.cancel.label = cancel_label

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user and interaction.user.id == self.author_id:
            return True
        else:
            await interaction.response.send_message(
                "This confirmation dialog is not for you.", ephemeral=True
            )
            return False

    async def on_timeout(self) -> None:
        if self.delete_after and self.message:
            await self.message.delete()
        for child in self.children:
            child.disabled = True
            child.style = discord.ButtonStyle.gray
        if self.message:
            await self.message.edit(view=self)

    @discord.ui.button(style=discord.ButtonStyle.green)
    async def confirm(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        self.value = True
        await interaction.response.defer()
        if self.delete_after:
            await interaction.delete_original_response()
        else:
            self.remove_item(self.cancel)
            button.disabled = True
            if self.message:
                await self.message.edit(view=self)
        self.stop()

    @discord.ui.button(style=discord.ButtonStyle.red)
    async def cancel(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.value = False
        await interaction.response.defer()
        if self.delete_after:
            await interaction.delete_original_response()
        else:
            self.remove_item(self.confirm)
            button.disabled = True
            if self.message:
                await self.message.edit(view=self)

        self.stop()


class DisambiguatorView(discord.ui.View, Generic[T]):
    message: discord.Message
    selected: T

    def __init__(self, ctx: Context, data: list[T], entry: Callable[[T], Any]):
        super().__init__()
        self.ctx: Context = ctx
        self.data: list[T] = data

        options = []
        for i, x in enumerate(data):
            opt = entry(x)
            if not isinstance(opt, discord.SelectOption):
                opt = discord.SelectOption(label=str(opt))
            opt.value = str(i)
            options.append(opt)

        select = discord.ui.Select(options=options)

        select.callback = self.on_select_submit
        self.select = select
        self.add_item(select)

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.ctx.author.id:
            await interaction.response.send_message(
                "This select menu is not meant for you, sorry.", ephemeral=True
            )
            return False
        return True

    async def on_select_submit(self, interaction: discord.Interaction):
        index = int(self.select.values[0])
        self.selected = self.data[index]
        await interaction.response.defer()
        if not self.message.flags.ephemeral:
            await self.message.delete()

        self.stop()


class Context(commands.Context):
    channel: Union[
        discord.VoiceChannel, discord.TextChannel, discord.Thread, discord.DMChannel
    ]
    prefix: str
    command: commands.Command[Any, Any]
    bot: UniversityBot

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    async def entry_to_code(self, entries: Iterable[tuple[str, str]]) -> None:
        width = max(len(a) for a, b in entries)
        output = ["```"]
        for name, entry in entries:
            output.append(f"{name:<{width}}: {entry}")
        output.append("```")
        await self.send("\n".join(output))

    async def indented_entry_to_code(self, entries: Iterable[tuple[str, str]]) -> None:
        width = max(len(a) for a, b in entries)
        output = ["```"]
        for name, entry in entries:
            output.append(f"\u200b{name:>{width}}: {entry}")
        output.append("```")
        await self.send("\n".join(output))

    def __repr__(self) -> str:
        # we need this for our cache key strategy
        return "<Context>"

    @property
    def session(self) -> aiohttp.ClientSession:
        return self.bot.session

    @discord.utils.cached_property
    def replied_reference(self) -> Optional[discord.MessageReference]:
        ref = self.message.reference
        if ref and isinstance(ref.resolved, discord.Message):
            return ref.resolved.to_reference()
        return None

    @discord.utils.cached_property
    def replied_message(self) -> Optional[discord.Message]:
        ref = self.message.reference
        if ref and isinstance(ref.resolved, discord.Message):
            return ref.resolved
        return None

    async def disambiguate(
        self, matches: list[T], entry: Callable[[T], Any], *, ephemeral: bool = False
    ) -> T:
        if len(matches) == 0:
            raise ValueError("No results found.")

        if len(matches) == 1:
            return matches[0]

        if len(matches) > 25:
            raise ValueError("Too many results... sorry.")

        view = DisambiguatorView(self, matches, entry)
        view.message = await self.send(
            "There are too many matches... Which one did you mean?",
            view=view,
            ephemeral=ephemeral,
        )
        await view.wait()
        return view.selected

    async def prompt(
        self,
        message: str,
        *,
        timeout: float = 60.0,
        delete_after: bool = True,
        author_id: Optional[int] = None,
        confirm_label: str = "Confirm!",
        cancel_label: str = "Cancel",
        am: discord.AllowedMentions | None = None,
        ephemeral: bool = True,
    ) -> Optional[bool]:
        """An interactive reaction confirmation dialog.

        Parameters
        -----------
        message: str
            The message to show along with the prompt.
        timeout: float
            How long to wait before returning.
        delete_after: bool
            Whether to delete the confirmation message after we're done.
        author_id: Optional[int]
            The member who should respond to the prompt. Defaults to the author of the
            Context's message.
        confirm_label: str
            The confirm label
        cancel_label: str
            The cancel label
        am: discord.AllowedMentions | None
            What mentions to use, if any
        ephemeral: bool
            Whether or not to make the message ephemeral

        Returns
        --------
        Optional[bool]
            ``True`` if explicit confirm,
            ``False`` if explicit deny,
            ``None`` if deny due to timeout
        """

        author_id = author_id or self.author.id
        view = ConfirmationView(
            timeout=timeout,
            delete_after=delete_after,
            author_id=author_id,
            confirm_label=confirm_label,
            cancel_label=cancel_label,
        )
        view.message = await self.send(
            message, view=view, ephemeral=ephemeral, allowed_mentions=am
        )
        await view.wait()
        return view.value

    def humanize_list(self, items: Sequence[str]) -> str:
        if type(items) != list:
            items = list(items)
        if len(items) == 1:
            return items[0]
        return ", ".join(items[:-1]) + (", and ") + items[-1]

    def tick(self, opt: Optional[bool], label: Optional[str] = None) -> str:
        lookup = {True: "success", False: "error", None: "info"}

        emoji = self.bot.themes.get_emoji_for(
            lookup.get(opt), theme=self.bot.main_config.get("theme", "default")
        )
        if label is not None:
            return f"{emoji}: {label}"
        return emoji

    async def show_help(self, command: Any = None) -> None:
        """Shows the help command for the specified command if given.

        If no command is given, then it'll show help for the current
        command.
        """
        cmd = self.bot.get_command("help")
        command = command or self.command.qualified_name
        await self.invoke(cmd, command=command)  # type: ignore

    async def safe_send(
        self, content: str, *, escape_mentions: bool = True, **kwargs
    ) -> discord.Message:
        """Same as send except with some safe guards.

        1) If the message is too long then it sends a file with the results instead.
        2) If ``escape_mentions`` is ``True`` then it escapes mentions.
        """
        if escape_mentions:
            content = discord.utils.escape_mentions(content)

        if len(content) > 2000:
            fp = io.BytesIO(content.encode())
            kwargs.pop("file", None)
            return await self.send(
                file=discord.File(fp, filename="message_too_long.txt"), **kwargs
            )
        else:
            return await self.send(content)

    async def send_embed(
        self,
        style: str,
        content: str,
        eph: bool = False,
        reply: bool = False,
        view: discord.ui.View = None,
        theme: str = None,
    ):
        """
        Makes and sends our embed, this allows for custom color, emoji etc.
        """
        mode = self.send
        if reply:
            mode = self.reply
        embed = discord.Embed(description=content, colour=discord.Colour.blurple())
        return await mode(embed=embed, mention_author=reply, ephemeral=eph, view=view)


class GuildContext(Context):
    author: discord.Member
    guild: discord.Guild
    channel: Union[discord.VoiceChannel, discord.TextChannel, discord.Thread]
    me: discord.Member
    prefix: str
