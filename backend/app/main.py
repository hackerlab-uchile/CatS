from fastapi import FastAPI, Depends
from typing import List
from models import Community
from database import engine, SessionLocal, Base
from sqlalchemy.orm import Session
import schemas

app = FastAPI() # instance of FastAPI
Base.metadata.create_all(bind=engine)

app.title = "CatS"
app.version = "1.0.0"

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# path
@app.get("/communities/", response_model=List[schemas.Community])
def read_communities(db: Session = Depends(get_db)):
    return db.query(Community).all()

@app.post("/communities/", response_model=schemas.Community)
def create_community(community: schemas.CommunityCreate, db: Session = Depends(get_db)):
    db_community = Community(**community.model_dump())
    db.add(db_community)
    db.commit()
    db.refresh(db_community)
    return db_community