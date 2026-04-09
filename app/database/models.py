from sqlalchemy import Column, String, Integer, DateTime
from app.database.db import Base
from datetime import datetime

class AttendanceRecord(Base):
    __tablename__ = "attendance"

    id         = Column(Integer, primary_key=True, autoincrement=True)
    roll_no    = Column(String, nullable=False)
    name       = Column(String, nullable=False)
    date       = Column(String, nullable=False)
    time       = Column(String, nullable=False)
    lecture    = Column(String, nullable=False)
    slot       = Column(String, nullable=False)
    subject    = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.now)