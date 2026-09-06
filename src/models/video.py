from datetime import date

from pydantic import BaseModel


class Video(BaseModel):
    num: int
    title: str
    url: str | None
    reserve_url: str | None
    image_file: str | None
    description: str | None
    quality: str
    published: date
