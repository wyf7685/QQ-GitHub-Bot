"""Milky matchers for the multi-pod status plugin."""

from nonebot import on_type
from nonebot_plugin_status import status_permission
from nonebot.adapters.milky.event import GroupNudgeEvent, FriendNudgeEvent

from . import server_status


def is_nudge_to_me(event: FriendNudgeEvent | GroupNudgeEvent) -> bool:
    if isinstance(event, FriendNudgeEvent):
        return event.data.is_self_receive
    return event.data.receiver_id == event.self_id


nudge = on_type(
    (FriendNudgeEvent, GroupNudgeEvent),
    rule=is_nudge_to_me,
    permission=status_permission,
    priority=10,
    block=True,
    handlers=[server_status],
)
"""Show aggregated status when the bot receives a Milky nudge."""
