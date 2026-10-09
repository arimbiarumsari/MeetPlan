from fastapi import FastAPI
from app.routers import events, members, status, recommend

app = FastAPI(title="MeetPlan API")

app.include_router(events.router)
app.include_router(members.router)
app.include_router(status.router)
app.include_router(recommend.router)

@app.get("/")
def root():
    return {"message": "MeetPlan API is running"}