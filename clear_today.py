from app.database.db import SessionLocal
from app.database.models import AttendanceRecord
from datetime import datetime

db = SessionLocal()

today = datetime.now().strftime("%Y-%m-%d")

db.query(AttendanceRecord).filter_by(date=today).delete()
db.commit()

print("✅ Today's attendance cleared")

db.close()