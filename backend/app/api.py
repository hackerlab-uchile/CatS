from database import get_db
from fastapi import Depends
from typing import List
from main import app
from models import Community
from sqlalchemy.orm import Session
import schemas

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