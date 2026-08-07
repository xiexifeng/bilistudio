from sqlalchemy import Column, Integer, String, DateTime, Text, BigInteger
from database import Base
from datetime import datetime

class Collection(Base):
    __tablename__ = "collection"

    id = Column(Integer, primary_key=True, index=True)
    bvid = Column(String(20), unique=True, index=True, nullable=False)
    title = Column(String(500), nullable=False)
    author = Column(String(200), nullable=False, index=True)
    author_mid = Column(BigInteger, nullable=True)
    pic = Column(String(500), nullable=True)
    duration = Column(String(20), nullable=True)
    description = Column(Text, nullable=True)
    play_count = Column(BigInteger, nullable=True)
    pubdate = Column(String(20), nullable=True)
    note = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
