from pydantic import BaseModel, ConfigDict


class CountryBase(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    owner_id: str | None

    # Пока не отдаём: на фронте эти поля не используются.
    # Оставляем здесь на будущее.
    # begin_year: int
    # end_year: int | None
    # deleted: bool


class Country(CountryBase):
    pass
    # Пока не отдаём и не тянем связи с бэка.
    # owner: CountryBase | None = None
    # regions: list[CountryBase] = Field(default_factory=list)
