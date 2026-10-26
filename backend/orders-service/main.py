
from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from prometheus_fastapi_instrumentator import Instrumentator

from src.api import order_router
from src.config import settings
from src.database import engine
from src.exceptions import OrderError
from src.producer import broker


@asynccontextmanager
async def lifespan(app: FastAPI):
    await broker.start()
    yield
    await engine.dispose()
    await broker.close()


app = FastAPI(
    lifespan=lifespan,
    root_path='/api',
    docs_url="/orders/docs",
    redoc_url="/orders/redoc",
    openapi_url="/orders/openapi.json",
)

if settings.CORS_ORIGINS:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

app.include_router(order_router)

Instrumentator().instrument(app).expose(app)


@app.exception_handler(OrderError)
async def app_exception_handler(request: Request, exc: OrderError):
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
