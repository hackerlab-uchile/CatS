from pydantic import BaseModel
from typing import List, Optional

class UrlBase(BaseModel):
    url: str
    justification: Optional[str]

class UrlCreate(UrlBase):
    community_id: int

class Url(UrlBase):
    id: int
    community_id: int

    class Config:
        orm_mode = True

class TagBase(BaseModel):
    name: str
    action: Optional[str]

class TagCreate(TagBase):
    community_id: int

class Tag(TagBase):
    id: int
    community_id: int

    class Config:
        orm_mode = True

class CommunityBase(BaseModel):
    name: str
    ip: str
    description: Optional[str]
    total_followers: Optional[int]

class CommunityCreate(CommunityBase):
    pass

class Community(CommunityBase):
    id: int
    created_date: str
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
