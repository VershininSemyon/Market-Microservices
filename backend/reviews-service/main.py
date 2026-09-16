
from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from prometheus_fastapi_instrumentator import Instrumentator

from src.api import review_router
from src.config import settings
from src.database import engine
from src.exceptions import ReviewError
from src.producer import rabbitmq_producer


@asynccontextmanager
async def lifespan(app: FastAPI):
    await rabbitmq_producer.connect()
    yield
    await engine.dispose()
    await rabbitmq_producer.close()


app = FastAPI(
    lifespan=lifespan,
    root_path='/api',
    docs_url="/reviews/docs",
    redoc_url="/reviews/redoc",
    openapi_url="/reviews/openapi.json",
)

if settings.CORS_ORIGINS:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

app.include_router(review_router)

Instrumentator().instrument(app).expose(app)


@app.exception_handler(ReviewError)
async def app_exception_handler(request: Request, exc: ReviewError):
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail},
    )


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        reload=settings.UVICORN_RELOAD,
        workers=settings.UVICORN_WORKERS_COUNT
    )
