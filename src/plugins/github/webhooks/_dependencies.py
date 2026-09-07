"""
@Author         : yanyongyu
@Date           : 2022-11-07 08:35:10
@LastEditors    : yanyongyu
@LastEditTime   : 2024-06-02 16:52:21
@Description    : Webhook dependencies
@GitHub         : https://github.com/yanyongyu
"""

__author__ = "yanyongyu"

from datetime import timedelta
from typing import Generic, TypeVar, Annotated, TypeAlias

from nonebot import logger
from nonebot.params import Depends
from nonebot.matcher import Matcher
from nonebot.adapters.github import Event
from nonebot_plugin_alconna import UniMessage
from nonebot.adapters.github.utils import get_attr_or_item
from nonebot.adapters.qq.exception import ActionFailed as QQOfficialActionFailed

from src.providers.redis import redis_client
from src.plugins.github.models import Subscription
from src.providers.platform import extract_sent_message
from src.plugins.github.helpers import build_image_message
from src.plugins.github.cache.message_tag import Tag, create_message_tag

T = TypeVar("T", bound=Event)

SEND_INTERVAL = 0.5
THROTTLE_KEY = "cache:github:webhooks:throttle:{identifier}"


async def get_event_info(
    event: Event, matcher: Matcher
) -> tuple[str, str, str, str | None]:
    repository = get_attr_or_item(event.payload, "repository")
    full_name = get_attr_or_item(repository, "full_name")
    if not repository or not full_name:
        await matcher.finish()
    owner, repo = full_name.split("/", 1)
    action = get_attr_or_item(event.payload, "action")
    if not all((owner, repo, event.name)):
        await matcher.finish()
    return owner, repo, event.name, action


EVENT_INFO: TypeAlias = Annotated[
    tuple[str, str, str, str | None], Depends(get_event_info)
]


async def list_subscribers(event_info: EVENT_INFO) -> list[Subscription]:
    owner, repo, event_name, action = event_info
    return await Subscription.list_subscribers(owner, repo, event_name, action)


SUBSCRIBERS: TypeAlias = Annotated[list[Subscription], Depends(list_subscribers)]


async def send_subscriber_message(
    subscription: Subscription, message: UniMessage, tag: Tag
) -> None:
    delivery_target = subscription.to_delivery_target()
    if delivery_target is None:
        logger.error(
            "Unable to build subscriber delivery target",
            target_info=subscription.to_subscriber_info(),
        )
        return

    try:
        receipt = await delivery_target.to_target().send(message)
    except QQOfficialActionFailed as e:
        if e.code in (304045, 304046, 304047, 304048, 304049, 304050):
            return
        raise

    if sent_message_info := extract_sent_message(
        subscription.to_subscriber_info(), receipt
    ):
        await create_message_tag(sent_message_info, tag)


async def send_subscriber_text(subscription: Subscription, text: str, tag: Tag) -> None:
    await send_subscriber_message(subscription, UniMessage.text(text), tag)


async def send_subscriber_image(
    subscription: Subscription, image: bytes, tag: Tag
) -> None:
    await send_subscriber_message(subscription, await build_image_message(image), tag)


class Throttle(Generic[T]):
    def __init__(
        self,
        event_type: tuple[type[T], ...],
        expire: timedelta,
    ):
        self.event_type = event_type
        self.expire = expire

    @classmethod
    def get_key(cls, event: Event) -> str:
        username: str = get_attr_or_item(
            get_attr_or_item(event.payload, "sender"), "login"
        )
        action: str | None = get_attr_or_item(event.payload, "action")
        event_type: str = event.name + (f"/{action}" if action else "")
        repository = get_attr_or_item(event.payload, "repository")
        repo_name = repository and get_attr_or_item(repository, "full_name")
        identifier = f"{username}:{event_type}" + (f":{repo_name}" if repo_name else "")
        return THROTTLE_KEY.format(identifier=identifier)

    async def __call__(self, event: Event, matcher: Matcher):
        # do nothing to other event
        if not isinstance(event, self.event_type):
            return

        # check exists identity
        key = self.get_key(event)
        exists = await redis_client.get(key)
        if exists is not None:
            matcher.skip()
        else:
            await redis_client.set(key, 1, ex=self.expire)
