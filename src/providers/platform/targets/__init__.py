"""
@Author         : yanyongyu
@Date           : 2023-10-07 17:19:00
@LastEditors    : yanyongyu
@LastEditTime   : 2023-11-11 14:58:29
@Description    : None
@GitHub         : https://github.com/yanyongyu
"""

__author__ = "yanyongyu"

from typing import Annotated, TypeAlias

from pydantic import Field
from nonebot_plugin_alconna import Target, SupportScope, SupportAdapter

from ._base import TargetType as TargetType
from ._base import BaseTargetInfo as BaseTargetInfo
from ._base import DeliveryTargetInfo as DeliveryTargetInfo

# isort: split

from .user import UserInfo as UserInfo
from .user import QQUserInfo as QQUserInfo
from .user import BaseUserInfo as BaseUserInfo
from .user import QQGuildUserInfo as QQGuildUserInfo
from .user import QQOfficialUserInfo as QQOfficialUserInfo

# isort: split

from .group import GroupInfo as GroupInfo
from .group import QQGroupInfo as QQGroupInfo
from .group import BaseGroupInfo as BaseGroupInfo
from .group import QQGuildChannelInfo as QQGuildChannelInfo
from .group import QQOfficialGroupInfo as QQOfficialGroupInfo

TargetInfo: TypeAlias = Annotated[UserInfo | GroupInfo, Field(discriminator="type")]


def get_fallback_delivery_target(
    target_info: TargetInfo,
) -> DeliveryTargetInfo | None:
    """Build a best-effort route for subscriptions created before route storage."""

    match target_info:
        case QQUserInfo():
            target = Target.user(
                str(target_info.qq_user_id), scope=SupportScope.qq_client
            )
        case QQGroupInfo():
            target = Target.group(
                str(target_info.qq_group_id), scope=SupportScope.qq_client
            )
        case QQOfficialUserInfo():
            target = Target.user(
                target_info.qq_user_open_id,
                scope=SupportScope.qq_api,
                adapter=SupportAdapter.qq,
            )
        case QQOfficialGroupInfo():
            target = Target.group(
                target_info.qq_group_open_id,
                scope=SupportScope.qq_api,
                adapter=SupportAdapter.qq,
            )
        case QQGuildChannelInfo():
            target = Target.channel_(
                target_info.qq_channel_id,
                target_info.qq_guild_id,
                scope=SupportScope.qq_api,
                adapter=SupportAdapter.qq,
            )
        case QQGuildUserInfo():
            return None
    return DeliveryTargetInfo.from_target(target)
