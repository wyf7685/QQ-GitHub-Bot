from typing import Literal

from pydantic import BaseModel, WebsocketUrl, PositiveFloat


class Config(BaseModel):
    playwright_ws_endpoint: WebsocketUrl
    playwright_browser_type: Literal["chromium", "firefox", "webkit"] = "chromium"
    playwright_connect_timeout: PositiveFloat = 30
