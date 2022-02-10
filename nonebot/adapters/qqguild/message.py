import re
from typing import Any, Type, Tuple, Union, Iterable

from nonebot.typing import overrides

from nonebot.adapters import Message as BaseMessage
from nonebot.adapters import MessageSegment as BaseMessageSegment

from .utils import escape, unescape
from .api import Message as GuildMessage
from .api import MessageArk, MessageEmbed


class MessageSegment(BaseMessageSegment["Message"]):
    @classmethod
    @overrides(BaseMessageSegment)
    def get_message_class(cls) -> Type["Message"]:
        return Message

    @staticmethod
    def ark(ark: MessageArk) -> "Ark":
        return Ark("ark", data={"ark": ark})

    @staticmethod
    def embed(embed: MessageEmbed) -> "Embed":
        return Embed("embed", data={"embed": embed})

    @staticmethod
    def emoji(id: int) -> "Emoji":
        return Emoji("emoji", data={"id": str(id)})

    @staticmethod
    def mention_user(user_id: str) -> "MentionUser":
        return MentionUser("mention_user", {"user_id": user_id})

    @staticmethod
    def mention_channel(channel_id: str) -> "MentionChannel":
        return MentionChannel("mention_channel", {"channel_id": channel_id})

    @staticmethod
    def text(content: str) -> "Text":
        return Text("text", {"text": content})

    @overrides(BaseMessageSegment)
    def is_text(self) -> bool:
        return self.type == "text"


class Text(MessageSegment):
    @overrides(MessageSegment)
    def __str__(self) -> str:
        return escape(self.data["text"])


class Emoji(MessageSegment):
    @overrides(MessageSegment)
    def __str__(self) -> str:
        return f"<emoji:{self.data['id']}>"


class MentionUser(MessageSegment):
    @overrides(MessageSegment)
    def __str__(self) -> str:
        return f"<@{self.data['user_id']}>"


class MentionEveryone(MessageSegment):
    @overrides(MessageSegment)
    def __str__(self) -> str:
        return "@everyone"


class MentionChannel(MessageSegment):
    @overrides(MessageSegment)
    def __str__(self) -> str:
        return f"#<{self.data['channel_id']}>"


class Attachment(MessageSegment):
    @overrides(MessageSegment)
    def __str__(self) -> str:
        return f"<attachment:{self.data['attachment']}>"


class Embed(MessageSegment):
    @overrides(MessageSegment)
    def __str__(self) -> str:
        return f"<embed:{self.data['embed']}>"


class Ark(MessageSegment):
    @overrides(MessageSegment)
    def __str__(self) -> str:
        return f"<ark:{self.data['ark']}>"


class Message(BaseMessage[MessageSegment]):
    @classmethod
    @overrides(BaseMessage)
    def get_segment_class(cls) -> Type[MessageSegment]:
        return MessageSegment

    @overrides(BaseMessage)
    def __add__(
        self, other: Union[str, MessageSegment, Iterable[MessageSegment]]
    ) -> "Message":
        return super(Message, self).__add__(
            MessageSegment.text(other) if isinstance(other, str) else other
        )

    @overrides(BaseMessage)
    def __radd__(
        self, other: Union[str, MessageSegment, Iterable[MessageSegment]]
    ) -> "Message":
        return super(Message, self).__radd__(
            MessageSegment.text(other) if isinstance(other, str) else other
        )

    @staticmethod
    @overrides(BaseMessage)
    def _construct(msg: str) -> Iterable[MessageSegment]:
        text_begin = 0
        for embed in re.finditer(
            r"\<@!?(?P<id>\w+?)\>",
            msg,
        ):
            yield Text("text", {"text": msg[text_begin : embed.pos + embed.start()]})
            text_begin = embed.pos + embed.end()
            yield MentionUser("mention_user", {"user_id": embed.group("id")})
        yield Text("text", {"text": msg[text_begin:]})

    @classmethod
    def from_guild_message(cls, message: GuildMessage) -> "Message":
        msg = Message()
        if message.content:
            msg.extend(Message(message.content))
        if message.attachments:
            msg.extend(
                Attachment("attachment", data={"attachment": seg})
                for seg in message.attachments
            )
        if message.embeds:
            msg.extend(Embed("embed", data={"embed": seg}) for seg in message.embeds)
        if message.ark:
            msg.append(Ark("ark", data={"ark": message.ark}))
        return msg
