"""
@Author         : yanyongyu
@Date           : 2023-10-07 17:19:34
@LastEditors    : yanyongyu
@LastEditTime   : 2024-03-05 14:51:27
@Description    : None
@GitHub         : https://github.com/yanyongyu
"""

__author__ = "yanyongyu"

from pydantic import BaseModel

from src.providers.platform.targets import TargetType


class MessageInfo(BaseModel):
    """Protocol-scoped message identity used by reply caches."""

    type: TargetType
    id: str
    adapter: str
    self_id: str
    target_id: str
    parent_id: str = ""
