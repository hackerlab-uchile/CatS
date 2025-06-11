from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

class UrlBase(BaseModel):
    url: str
    justification: Optional[str]

class UrlCreate(UrlBase):
    community_id: int
    tag_id: int

class Url(UrlBase):
    id: int
    community_id: int
    tag_id: int

    class Config:
        from_attributes = True

class TagBase(BaseModel):
    name: str
    action: Optional[str]
    description: Optional[str]

class TagCreate(TagBase):
    community_id: int

class Tag(TagBase):
    id: int
    community_id: int

    class Config:
        from_attributes = True

class CommunityBase(BaseModel):
    name: str
    description: Optional[str]

class CommunityCreate(CommunityBase):
    pass

class Community(CommunityBase):
    id: int
    created_date: datetime
    tags: List[Tag] = []
    urls: List[Url] = []

    class Config:
        from_attributes = True

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
        from_attributes = True
