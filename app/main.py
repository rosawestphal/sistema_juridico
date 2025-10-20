# app/main.py
from fastapi import FastAPI
from app.routers import processos
from app.db import init_db
import asyncio

app = FastAPI(title="Processos API")

app.include_router(processos.router)

@app.on_event("startup")
async def on_startup():
    await init_db()
