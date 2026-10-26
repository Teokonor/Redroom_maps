from typing import List

from fastapi import APIRouter

from ..database import TagService
from ..models.tag import Tag


tag_router = APIRouter(prefix='/tag', tags=['Tag'])


@tag_router.get('/all', response_model=List[Tag])
def get_all_tags():
    return TagService.get_all()
