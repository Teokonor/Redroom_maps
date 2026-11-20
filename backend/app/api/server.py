import os
from contextlib import asynccontextmanager
from time import perf_counter

from fastapi import FastAPI, Request
from fastapi.responses import Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from loguru import logger
from uvicorn import Server as UvicornServer, Config as UvicornConfig

from .country import country_router
from .data import data_router
from .geometry import map_router, warm_map_version
from .preview import preview_router
from .tag import tag_router
from .video import video_router


HOST = '0.0.0.0'
PORT = 8652


def _extra_cors_origins() -> list[str]:
    """Additional origins for a frontend served from another domain."""
    raw = os.environ.get('REDROOM_CORS_ORIGINS', '')

    return [
        item.strip().rstrip('/')
        for item in raw.split(',')
        if item.strip()
    ]


@asynccontextmanager
async def lifespan(_app: FastAPI):
    warm_map_version()
    yield


def create_app() -> FastAPI:
    app = FastAPI(title='Redroom Maps API', lifespan=lifespan)

    @app.get('/ping')
    def ping_server():
        return Response(status_code=200)

    @app.middleware('http')
    async def log_requests(request: Request, call_next):
        started_at = perf_counter()

        try:
            response = await call_next(request)
        except Exception:
            logger.exception(
                'Request failed: {} {}',
                request.method,
                request.url.path,
            )
            raise

        elapsed_ms = (perf_counter() - started_at) * 1000
        path = request.url.path
        message = '{} {} -> {} in {:.1f} ms'

        if response.status_code >= 400:
            logger.warning(
                message,
                request.method,
                path,
                response.status_code,
                elapsed_ms,
            )
        elif elapsed_ms >= 500:
            logger.warning(
                'Slow request: ' + message,
                request.method,
                path,
                response.status_code,
                elapsed_ms,
            )
        elif path.startswith(('/map/', '/preview/')):
            logger.debug(
                message,
                request.method,
                path,
                response.status_code,
                elapsed_ms,
            )
        else:
            logger.info(
                message,
                request.method,
                path,
                response.status_code,
                elapsed_ms,
            )

        return response

    app.add_middleware(
        CORSMiddleware,
        allow_origins=[
            'http://localhost:5173',
            'http://localhost:4173',
            *_extra_cors_origins(),
        ],
        # Access from a phone over the local network during development.
        allow_origin_regex=(
            r'https?://(?:localhost|127\.0\.0\.1|\[::1\]'
            r'|10\.\d{1,3}\.\d{1,3}\.\d{1,3}'
            r'|192\.168\.\d{1,3}\.\d{1,3}'
            r'|172\.(?:1[6-9]|2\d|3[01])\.\d{1,3}\.\d{1,3})'
            r'(?::\d+)?'
        ),
        allow_credentials=True,
        allow_methods=['*'],
        allow_headers=['*'],
    )
    app.add_middleware(GZipMiddleware, minimum_size=1024)
    app.include_router(map_router)
    app.include_router(data_router)
    app.include_router(country_router)
    app.include_router(preview_router)
    app.include_router(tag_router)
    app.include_router(video_router)

    return app


app = create_app()


def run_app():
    logger.info('Starting Uvicorn on {}:{}', HOST, PORT)

    server = UvicornServer(
        UvicornConfig(
            app,
            host=HOST,
            port=PORT,
            proxy_headers=True,
            forwarded_allow_ips='*',
            access_log=False,
        )
    )
    server.run()
