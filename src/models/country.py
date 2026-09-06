from pydantic import BaseModel


class Country(BaseModel):
    id: int
    name: str
    begin_year: int
    end_year: int | None
    owner_id: int | None
