"""FastAPI entry point for the bowling discipline route."""

from fastapi import FastAPI

from Droutes import router as discipline_router

app = FastAPI(title="Bowling Discipline API")
app.include_router(discipline_router)
