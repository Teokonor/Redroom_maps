from fastapi import FastAPI
from fastapi.responses import Response
from fastapi.middleware.cors import CORSMiddleware
from uvicorn import Server as UvicornServer, Config as UvicornConfig

from .country import country_router
from .geometry import map_router
from .tag import tag_router
from .video import video_router

def run_app():
    app = FastAPI()

    @app.get("/ping")
    def ping_server():
        return Response(status_code=200)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[
            "http://localhost:5173",
        ],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.include_router(map_router)
    app.include_router(country_router)
    app.include_router(tag_router)
    app.include_router(video_router)


    server = UvicornServer(
        UvicornConfig(
            app,
            host="0.0.0.0",
            port=8652,
            proxy_headers=True,
            forwarded_allow_ips='*'
        )
    )
    server.run()
