from datetime import datetime

from pydantic import BaseModel, StrictInt


class RateLimit(BaseModel):
    limit: StrictInt
    remaining: StrictInt
    image_limit: StrictInt
    image_remaining: StrictInt
    reset: StrictInt

    @property
    def reset_date(self) -> datetime:
        return datetime.fromtimestamp(self.reset)
