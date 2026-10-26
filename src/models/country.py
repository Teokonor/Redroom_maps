from typing import List

from pydantic import BaseModel, ConfigDict, Field


class CountryBase(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    begin_year: int
    end_year: int | None
    owner_id: str | None
    deleted: bool


class Country(CountryBase):
    owner: CountryBase | None = None
    regions: List[CountryBase] = Field(default_factory=list)
