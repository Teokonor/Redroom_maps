from datetime import date
from typing import List

from pydantic import BaseModel, ConfigDict


class Video(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    num: int
    title: str
    url: str | None
    reserve_url: str | None
    image_file: str | None
    description: str | None
    quality: str
    published: date


class VideoSelection(BaseModel):
    main: List[Video]
    indirectly: List[Video]
