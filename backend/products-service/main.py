
from contextlib import asynccontextmanager

import pydantic
import uvicorn
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from prometheus_fastapi_instrumentator import Instrumentator

from src.api import product_router
from src.config import settings
from src.database import engine
from src.exceptions import ProductError
from src.search import create_products_index


@asynccontextmanager
async def lifespan(app: FastAPI):
    await create_products_index()
    yield
    await engine.dispose()


app = FastAPI(
    lifespan=lifespan,
    root_path='/api',
    docs_url="/products/docs",
    redoc_url="/products/redoc",
    openapi_url="/products/openapi.json",
)

if settings.CORS_ORIGINS:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

app.include_router(product_router)

Instrumentator().instrument(app).expose(app)


@app.exception_handler(pydantic.ValidationError)
async def pydantic_validation_exception_handler(request: Request, exc: pydantic.ValidationError):
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
        content={"detail": exc.errors(include_url=False, include_context=False)},
    )

@app.exception_handler(ProductError)
async def app_exception_handler(request: Request, exc: ProductError):
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
