"""
@Author         : yanyongyu
@Date           : 2023-10-07 17:19:50
@LastEditors    : yanyongyu
@LastEditTime   : 2024-03-05 14:27:50
@Description    : None
@GitHub         : https://github.com/yanyongyu
"""

__author__ = "yanyongyu"

from typing import Any, Annotated, TypeAlias

from nonebot.params import Depends
from nonebot.adapters import Bot, Event
from nonebot_plugin_uninfo import Session
from nonebot_plugin_uninfo import get_session
from nonebot_plugin_uninfo import SupportScope as InfoScope
from nonebot_plugin_alconna.uniseg import Receipt, SerializeFailed
from nonebot_plugin_alconna import (
    Reply,
    Target,
    UniMessage,
    SupportAdapter,
    get_target,
    get_message_id,
)

from src.providers.platform.roles import RoleLevel
from src.providers.platform.messages import MessageInfo
from src.providers.platform.targets import (
    UserInfo,
    GroupInfo,
    QQUserInfo,
    TargetInfo,
    TargetType,
    QQGroupInfo,
    QQGuildUserInfo,
    DeliveryTargetInfo,
    QQGuildChannelInfo,
    QQOfficialUserInfo,
    QQOfficialGroupInfo,
)

SESSION: TypeAlias = Annotated[Session | None, Depends(get_session, use_cache=True)]


def extract_user(session: SESSION) -> UserInfo | None:
    if session is None:
        return None

    scope = InfoScope(session.scope)
    if scope == InfoScope.qq_client:
        return QQUserInfo(type=TargetType.QQ_USER, qq_user_id=int(session.user.id))
    if scope != InfoScope.qq_api:
        return None
    if session.scene.is_channel or session.scene.parent:
        return QQGuildUserInfo(
            type=TargetType.QQGUILD_USER,
            qqguild_user_id=session.user.id,
        )
    return QQOfficialUserInfo(
        type=TargetType.QQ_OFFICIAL_USER,
        qq_user_open_id=session.user.id,
    )


def extract_group(session: SESSION) -> GroupInfo | None:
    if session is None:
        return None

    scope = InfoScope(session.scope)
    if scope == InfoScope.qq_client and session.scene.is_group:
        return QQGroupInfo(
            type=TargetType.QQ_GROUP,
            qq_group_id=int(session.scene.id),
        )
    if scope != InfoScope.qq_api:
        return None
    if session.scene.is_group:
        return QQOfficialGroupInfo(
            type=TargetType.QQ_OFFICIAL_GROUP,
            qq_group_open_id=session.scene.id,
        )
    if session.scene.is_channel and session.scene.parent:
        return QQGuildChannelInfo(
            type=TargetType.QQGUILD_CHANNEL,
            qq_guild_id=session.scene.parent.id,
            qq_channel_id=session.scene.id,
        )
    return None


def extract_target(session: SESSION) -> TargetInfo | None:
    return extract_group(session) or extract_user(session)


def extract_is_private(session: SESSION) -> bool | None:
    return session.scene.is_private if session is not None else None


def extract_role(session: SESSION) -> RoleLevel | None:
    if session is None or session.scene.is_private:
        return None
    if session.member and (role := session.member.role):
        role_id = role.id.upper()
        if role_id == "OWNER":
            return RoleLevel.OWNER
        if "ADMINISTRATOR" in role_id:
            return RoleLevel.ADMIN
        return RoleLevel.MEMBER
    if session.scene.is_group:
        return RoleLevel.MEMBER
    return RoleLevel.GUEST


def extract_delivery_target(bot: Bot, event: Event) -> DeliveryTargetInfo | None:
    try:
        return DeliveryTargetInfo.from_target(get_target(event, bot))
    except (AssertionError, NotImplementedError, SerializeFailed):
        return None


def _adapter_name(adapter: Any) -> str:
    return str(getattr(adapter, "value", adapter))


def _message_info(
    session: Session | None, target: Target, message_id: str, bot: Bot
) -> MessageInfo | None:
    if (target_info := extract_target(session)) is None:
        return None
    return MessageInfo(
        type=target_info.type,
        id=message_id,
        adapter=_adapter_name(target.adapter or bot.adapter.get_name()),
        self_id=str(target.self_id or bot.self_id),
        target_id=target.id,
        parent_id=target.parent_id,
    )


def extract_message(bot: Bot, event: Event, session: SESSION) -> MessageInfo | None:
    try:
        target = get_target(event, bot)
        message_id = get_message_id(event, bot)
    except (AssertionError, NotImplementedError, SerializeFailed):
        return None
    return _message_info(session, target, message_id, bot)


async def extract_reply_message(
    bot: Bot, event: Event, session: SESSION
) -> MessageInfo | None:
    try:
        message = UniMessage.of(event.get_message(), bot=bot)
        await message.attach_reply(event, bot)
        if not message.has(Reply):
            return None
        reply = message[Reply, 0]
        target = get_target(event, bot)
    except (
        AssertionError,
        AttributeError,
        NotImplementedError,
        SerializeFailed,
        TypeError,
        ValueError,
    ):
        return None
    return _message_info(session, target, reply.id, bot)


def _sent_message_id(receipt: Receipt, target: Target) -> str | None:
    if reply := receipt.get_reply(0):
        message_id = reply.id
    elif receipt.msg_ids:
        raw = receipt.msg_ids[0]
        if isinstance(raw, dict):
            value = raw.get("message_id") or raw.get("id")
        else:
            value = getattr(raw, "id", None) or getattr(raw, "message_seq", None)
        message_id = str(value) if value is not None else ""
    else:
        return None

    if target.adapter == SupportAdapter.milky and "@" not in message_id:
        data = getattr(receipt.context, "data", None)
        scene = getattr(data, "message_scene", None)
        scene = scene or ("friend" if target.private else "group")
        return f"{message_id}@{scene}:{target.id}"
    return message_id or None


def extract_sent_message(target: TargetInfo, result: Any) -> MessageInfo | None:
    if not isinstance(result, Receipt):
        return None
    route = (
        result.context
        if isinstance(result.context, Target)
        else get_target(result.context, result.bot)
    )
    if (message_id := _sent_message_id(result, route)) is None:
        return None
    return MessageInfo(
        type=target.type,
        id=message_id,
        adapter=_adapter_name(route.adapter or result.bot.adapter.get_name()),
        self_id=str(route.self_id or result.bot.self_id),
        target_id=route.id,
        parent_id=route.parent_id,
    )
