from sqlalchemy import Column, ForeignKey, Integer, String, Text, DateTime, Table, BigInteger
from app.database import Base
from sqlalchemy.orm import relationship
from datetime import datetime

# Relation many-to-many between url and tag
tag_url = Table(
    "tag_url",
    Base.metadata,
    Column("tag_id", Integer, ForeignKey("tag.id", ondelete="CASCADE"), primary_key=True),
    Column("url_id", Integer, ForeignKey("url.id", ondelete="CASCADE"), primary_key=True),extend_existing=True
)

class Community(Base):
    __tablename__ = "community"  # Name of the table

    id = Column(BigInteger, primary_key=True, autoincrement=False)
    name = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    created_date = Column(DateTime, default=datetime.utcnow)

    # a community can have multiple tags
    tags = relationship("Tag", back_populates="community")
    urls = relationship("Url", back_populates="community")

class Tag(Base):
    __tablename__ = "tag"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, nullable=False)
    action = Column(String, nullable=False)
    description = Column(Text, nullable=False)
    community_id = Column(BigInteger, ForeignKey("community.id", ondelete="CASCADE"))

    community = relationship("Community", back_populates="tags")
    urls = relationship("Url", secondary=tag_url, back_populates="tags")

class Url(Base):
    __tablename__ = "url"

    id = Column(Integer, primary_key=True, autoincrement=True)
    url = Column(String, nullable=False, unique=True)
    justification = Column(Text, nullable=False)
    community_id = Column(BigInteger, ForeignKey("community.id", ondelete="CASCADE"))
    tag_id = Column(Integer, ForeignKey("tag.id", ondelete="CASCADE"))

    community = relationship("Community", back_populates="urls")
    tags = relationship("Tag", secondary=tag_url, back_populates="urls")
    revisions = relationship("Revision", back_populates="url")

class Revision(Base):
    __tablename__ = "revision"

    id = Column(Integer, primary_key=True, autoincrement=True)
    anonymous_user = Column(String, nullable=False)
    url_id = Column(Integer, ForeignKey("url.id", ondelete="CASCADE"))
    justification = Column(Text, nullable=True)
    status = Column(String, nullable=True)

    url = relationship("Url", back_populates="revisions")