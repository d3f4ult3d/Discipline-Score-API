"""
Match Scoreboard API — Entry Point
Run: uvicorn main:app --reload
"""
from fastapi import FastAPI
from Sroutes import router as scoreboard_router
from Iroutes import router as innings_router
from Eroutes import router as extras_router
from Wroutes import router as wicket_router
from Droutes import router as discipline_router

app = FastAPI(
    title="Match Scoreboard API",
    description=(
        "Live scoreboard and innings analytics. Returns frontend-ready JSON "
        "for the scoring page, live stream page, and AI agent tooling."
    ),
    version="1.0.0",
)

app.include_router(discipline_router, prefix="/api/v1", tags=["Discipline"])


@app.get("/health", tags=["Health"])
def health():
    return {"status": "ok"}
