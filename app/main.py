from fastapi import FastAPI
from app.routers import events, members

app = FastAPI(title="MeetPlan API")

app.include_router(events.router)
app.include_router(members.router)

@app.get("/")
def root():
    return {"message": "MeetPlan API is running"}