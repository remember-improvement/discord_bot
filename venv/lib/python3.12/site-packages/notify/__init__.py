from io import BufferedReader, BytesIO
from typing import Any, Dict, Union

import requests
from pydantic import BaseModel, StrictStr
from requests import Response

from notify.models.rate_limit import RateLimit
from notify.models.status import Status


class Notify(BaseModel):
    token: StrictStr
    host: StrictStr = "https://notify-api.line.me"

    def model_post_init(self, __context: Any) -> None:
        try:
            self.get_status()
        except KeyError:
            raise Exception("Invalid access token")

    @property
    def headers(self) -> Dict[str, str]:
        return {
            "Authorization": f"Bearer {self.token}",
        }

    def send_image_with_url(self, text: StrictStr, url: StrictStr) -> Response:
        image_data = BytesIO()
        r = requests.get(url)
        r.raise_for_status()
        image_data.write(r.content)
        image_data.seek(0)
        return self.send_image(text, image_data)

    def send_image_with_local_path(
        self, text: StrictStr, path: StrictStr
    ) -> Response:
        return self.send_image(text, open(path, "rb"))

    def send_image(
        self, text: StrictStr, image: Union[BufferedReader, BytesIO]
    ) -> Response:
        return self.send(
            {
                "message": (None, text),
                "imageFile": image,
            }
        )

    def send_text(self, text: str) -> Response:
        return self.send({"message": (None, text)})

    def send(self, files: Dict[str, Any]) -> Response:
        return requests.post(
            f"{self.host}/api/notify",
            headers=self.headers,
            files=files,
        )

    def revoke(self) -> Response:
        return requests.post(f"{self.host}/api/revoke", headers=self.headers)

    def get_status(self) -> Status:
        j: Dict[str, Any] = requests.get(
            f"{self.host}/api/status", headers=self.headers
        ).json()
        j["target_type"] = j.pop("targetType")
        return Status(**j)

    def get_rate_limit(self) -> RateLimit:
        headers = requests.head(
            f"{self.host}/api/status", headers=self.headers
        ).headers
        return RateLimit(
            limit=int(headers["X-RateLimit-Limit"]),
            remaining=int(headers["X-RateLimit-Remaining"]),
            image_limit=int(headers["X-RateLimit-ImageLimit"]),
            image_remaining=int(headers["X-RateLimit-ImageRemaining"]),
            reset=int(headers["X-RateLimit-Reset"]),
        )
