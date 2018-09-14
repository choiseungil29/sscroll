from sqlalchemy import Column, String, Integer, DateTime, Enum, ARRAY, ForeignKey
from sqlalchemy.orm import relationship

from db import Base

from datetime import datetime, timedelta


class Board(Base):
    """
    자유게시판 글
    """

    __tablename__ = 'boards'

    id = Column(Integer, primary_key=True)
    title = Column(String)
    data = Column(String)
    created_at = Column(DateTime)

    def __init__(self, **kwargs):
        Base.__init__(self, **kwargs)

        self.created_at = datetime.utcnow() + timedelta(hours=9)
