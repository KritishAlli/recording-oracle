from fastapi import FastAPI
from contextlib import asynccontextmanager
from database import init_db, Meeting, Transcript, LocalSession

# on startup, initialize database
@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db() 
    yield

app = FastAPI(lifespan=lifespan)

@app.get("/health")
def health():
    return {"status": "ok"}

# create one new meeting
@app.post("/meetings")
def create_meeting(title: str):
    db = LocalSession()
    new_meeting = Meeting(title=title, status="pending")
    db.add(new_meeting)
    db.commit()
    db.refresh(new_meeting)
    db.close()
    return {"id": new_meeting.id, "title": new_meeting.title, "status": new_meeting.status}

# get all meetings
@app.get("/meetings")
def get_meetings():
    db = LocalSession()
    meetings = db.query(Meeting).all()
    db.close()
    out = []
    for m in meetings:
        out.append({"id": m.id, "title": m.title, "status": m.status})
    return out
