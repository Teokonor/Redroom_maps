from typing import List

from fastapi import APIRouter

from ..models.country import Country
from ..database import CountryService


country_router = APIRouter(prefix='/country', tags=['Country'])


@country_router.get('/all', response_model=List[Country])
def get_all_countries():
    return CountryService.get_all()
