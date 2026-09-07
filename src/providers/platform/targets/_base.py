"""
@Author         : yanyongyu
@Date           : 2023-10-07 17:19:08
@LastEditors    : yanyongyu
@LastEditTime   : 2023-11-11 14:58:02
@Description    : None
@GitHub         : https://github.com/yanyongyu
"""

__author__ = "yanyongyu"

from enum import StrEnum
from typing import Any, Self

from pydantic import Field, BaseModel
from nonebot_plugin_alconna import Target


class TargetType(StrEnum):
    # User
    QQ_USER = "qq_user"
    QQ_OFFICIAL_USER = "qq_official_user"
    QQGUILD_USER = "qqguild_user"

    # Group
    QQ_GROUP = "qq_group"
    QQ_OFFICIAL_GROUP = "qq_official_group"
    QQGUILD_CHANNEL = "qqguild_channel"


class BaseTargetInfo(BaseModel):
    type: TargetType


class DeliveryTargetInfo(BaseModel):
    """Stable, serializable route used for proactive delivery."""

    id: str
    parent_id: str = ""
    channel: bool = False
    private: bool = False
    self_id: str | None = None
    scope: str | None = None
    adapter: str | None = None
    platforms: list[str] | None = None
    extra: dict[str, Any] = Field(default_factory=dict)

    @classmethod
    def from_target(cls, target: Target) -> Self:
        data = target.dump()
        data["extra"] = {}
        return cls.model_validate(data)

    def to_target(self) -> Target:
        return Target.load(self.model_dump(exclude_none=True))
