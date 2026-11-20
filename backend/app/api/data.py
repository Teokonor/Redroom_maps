from fastapi import APIRouter
from fastapi.responses import PlainTextResponse

from ..database import Database


data_router = APIRouter(prefix='/data', tags=['Data'])


@data_router.get('/version')
def get_data_version():
    return PlainTextResponse(
        Database.data_version(),
        headers={'Cache-Control': 'no-store'},
    )
