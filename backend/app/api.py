# app/api.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from app.database import get_db
from app.models import Community, Tag, Url
from app import schemas

router = APIRouter()

# Router for get communities
@router.get("/communities/", response_model=List[schemas.Community])
def read_communities(db: Session = Depends(get_db)):
    return db.query(Community).all()

# Router for get tags of an specific community
@router.get("/communities/{community_id}/tags", response_model=List[schemas.Tag])
def get_tags_by_community(community_id: int, db: Session = Depends(get_db)):
    tags = db.query(Tag).filter(Tag.community_id == community_id).all()
    if not tags:
        raise HTTPException(status_code=404, detail="No se encontraron tags")
    return tags

# Router for get urls from a specific tag of a specific community
@router.get("/communities/{community_id}/{tag_id}/urls", response_model=List[schemas.Url])
def get_urls_by_tag(community_id: int, tag_id: int, db: Session = Depends(get_db)):
    urls = db.query(Url).filter(
        Url.community_id == community_id,
        Url.tag_id == tag_id
    ).all()
    if not urls:
        raise HTTPException(status_code=404, detail="No se encontraron urls")
    return urls
