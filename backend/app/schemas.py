from pydantic import BaseModel
from typing import List, Optional
from sqlalchemy import BigInteger, DateTime, Integer

class UrlBase(BaseModel):
    url: str
    justification: Optional[str]

class UrlCreate(UrlBase):
    community_id: BigInteger
    tag_id: Integer

class Url(UrlBase):
    id: int
    community_id: BigInteger
    tag_id: Integer

    class Config:
        orm_mode = True

class TagBase(BaseModel):
    name: str
    action: Optional[str]
    description: Optional[str]

class TagCreate(TagBase):
    community_id: BigInteger

class Tag(TagBase):
    id: int
    community_id: BigInteger

    class Config:
        orm_mode = True

class CommunityBase(BaseModel):
    name: str
    description: Optional[str]

class CommunityCreate(CommunityBase):
    pass

class Community(CommunityBase):
    id: BigInteger
    created_date: DateTime
    tags: List[Tag] = []
    urls: List[Url] = []

    class Config:
        orm_mode = True

class RevisionBase(BaseModel):
    anonymous_user: str
    justification: Optional[str]
    status: Optional[str]

class RevisionCreate(RevisionBase):
    url_id: int

class Revision(RevisionBase):
    id: int
    url_id: int

    class Config:
        orm_mode = True
