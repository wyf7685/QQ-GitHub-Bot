from nonebot_plugin_alconna.uniseg import Receipt
from nonebot_plugin_alconna import Target, UniMessage

from src.providers.filehost import save_image

INLINE_IMAGE_MAX_SIZE = 2 * 1024 * 1024


async def build_image_message(image: bytes) -> UniMessage:
    if len(image) > INLINE_IMAGE_MAX_SIZE:
        return UniMessage.image(url=await save_image(image))
    return UniMessage.image(raw=image)


async def send_image(image: bytes, target: Target | None = None) -> Receipt:
    return await (await build_image_message(image)).send(target)
