from pydantic import BaseModel, ConfigDict


class Period(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    video_num: int
    country_id: str
    begin_year: int
    end_year: int
    is_main: bool


class PeriodGroup(BaseModel):
    begin_year: int
    end_year: int
    is_main: bool
    video_nums: list[int]
