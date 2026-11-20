from datetime import date

from pydantic import BaseModel, ConfigDict

from .period import PeriodGroup


class Video(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    num: int
    title: str
    url: str | None
    reserve_url: str | None
    image_file: str | None
    description: str | None
    mentioned: list[int] | None = None
    ideas_released: list[int] | None = None
    ideas_planned: list[str] | None = None
    quality: str
    published: date


class VideoSelection(BaseModel):
    main: list[Video]
    indirectly: list[Video]


class HistoryVideoSelection(VideoSelection):
    periods: list[PeriodGroup]
