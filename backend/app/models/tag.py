from pydantic import BaseModel, ConfigDict


class Tag(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    video_count: int
