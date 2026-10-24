

from fastapi import APIRouter, Depends, status

order_router = APIRouter(prefix="/orders", tags=["Orders"])
