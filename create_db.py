from app.db import Base, engine, SessionLocal
from app import models
from app.models import Job, Operation

Base.metadata.create_all(bind=engine)
print("created tables:", list(Base.metadata.tables))

db = SessionLocal()
job = Job(operation=Operation.resize, source_path="/tmp/in.png", target_width=800, target_height=600)
db.add(job); 
db.commit(); 
db.refresh(job)
print(job.id, job.status, job.created_at)
db.close()