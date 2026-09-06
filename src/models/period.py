from pydantic import BaseModel

class Period(BaseModel):
    id: int
    video_num: int
    country_id: str
    begin_year: int
    end_year: int | None
    is_main: bool
