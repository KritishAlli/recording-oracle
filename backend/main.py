from fastapi import FastAPI, UploadFile, File, HTTPException
from contextlib import asynccontextmanager
from database import init_db, Meeting, Transcript, LocalSession
import boto3
import uuid
import os
from openai import OpenAI
import tempfile


client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
s3 = boto3.client(
    "s3",
    region_name=os.environ.get("AWS_REGION")
)
S3_BUCKET = os.environ.get("S3_BUCKET_NAME")

# on startup, initialize database
@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db() 
    yield

app = FastAPI(lifespan=lifespan)


# here we are only uploading to an existing meeting (an update operation)
# keeps crud endpoints separate
# if multiple tries are necessary, doesn't add many new rows to our dataset
@app.post("/meetings/{meeting_id}/upload")
async def upload_file(meeting_id: int, file: UploadFile = File(...)):

    db = LocalSession()
    meeting = db.query(Meeting).filter(Meeting.id == meeting_id).first()
    if not meeting:
        db.close()
        raise HTTPException(status_code=404, detail="Meeting not found")
    
    # make a unique s3 key
    # filetype stores the filetype of the file
    # ex: "helloworld.txt"
    file_type = file.filename.split(".")[-1]
    s3_key = f"meetings/{meeting_id}/{uuid.uuid4()}.{file_type}"


    # try to upload to s3 bucket

    try:
        s3.upload_fileobj(file.file, S3_BUCKET, s3_key)
    except Exception as e:
        db.close()
        raise HTTPException(status_code=500, detail="File upload failed" + str(e) )


    # update the status of the meeting in table

    meeting.s3_key = s3_key
    meeting.status = "uploaded"
    db.commit()
    db.refresh(meeting)
    db.close()

    return {
        "meeting_id": meeting_id,
        "s3_key": s3_key,
        "status": meeting.status
    }

@app.post("/meetings/{meeting_id}/transcribe")
async def transcribe_file(meeting_id: int):
    db = LocalSession()
    meeting = db.query(Meeting).filter(Meeting.id == meeting_id).first()
    if not meeting:
        db.close()
        raise HTTPException(status_code=404, detail="Meeting not found")
    
    s3_key = meeting.s3_key

    file_type = s3_key.split(".")[-1]
    with tempfile.NamedTemporaryFile(suffix=f".{file_type}", delete=False) as tmp:
        s3.download_fileobj(S3_BUCKET, meeting.s3_key, tmp)
        tmp_path = tmp.name
    
    # call openAI's whisper API
    meeting.status = "transcribing"
    db.commit()
    with open(tmp_path, "rb") as audio_file:
        result = client.audio.transcriptions.create(
            model="whisper-1",
            file=audio_file,
            response_format="verbose_json"
        )
    meeting.status = "transcribed"
    for segment in result.segments:
        transcript = Transcript(
            meeting_id = meeting_id,
            speaker = "Unknown",
            text=segment.text,
            timestamp = segment.start
        )
        db.add(transcript)
        db.commit()
        db.refresh(transcript)

    db.close()
    return {
        "meeting_id": meeting_id,
        "status": "transcribed",
        "first_result": result.segments[0].text
    }

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
@app.get("/meetings/{meeting_id}/transcripts")
def get_transcripts(meeting_id: int):
    db = LocalSession()
    transcripts = db.query(Transcript).filter(Transcript.meeting_id == meeting_id).all()
    db.close()
    out = []
    for t in transcripts:
        out.append({"speaker": t.speaker, "text": t.text, "time": t.timestamp})
    return out