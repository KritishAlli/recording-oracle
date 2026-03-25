from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os
import time
from datetime import datetime


DATABASE_URL = os.environ.get("DATABASE_URL", "postgresql://postgres:password@localhost:5432/meetingdb")

engine = create_engine(DATABASE_URL)
LocalSession = sessionmaker(bind=engine)
Base = declarative_base()

class Meeting(Base):
    __tablename__ = "meetings"
    id = Column(Integer, primary_key = True)
    title = Column(String)
    status = Column(String, default="pending")
    created_at = Column(DateTime, default = datetime.utcnow())

class Transcript(Base):
    __tablename__ = "transcripts"
    id = Column(Integer, primary_key = True)
    meeting_id = Column(Integer, ForeignKey("meetings.id"))
    speaker = Column(String)
    text = Column(String)
    timestamp = Column(Float)


def init_db():
    for retry in range(10):
        try: 
            Base.metadata.create_all(engine)
            return
        except Exception as e:
            time.sleep(5)
            print(f"Initialization failed. Retrying... {e}")
