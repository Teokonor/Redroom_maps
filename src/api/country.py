from typing import List

from fastapi import APIRouter

from ..models import Country
from ..database import CountryService


map_router = APIRouter(prefix='/country', tags=['Country'])

@map_router.get('/all', response_model=List[Country], response_model_exclude_none=True)
def get_map_geometry():
    return CountryService.get_all()
