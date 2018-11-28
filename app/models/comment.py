from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, String, Integer, DateTime, Enum, ARRAY, ForeignKey
from sqlalchemy.orm import relationship

from db import Base


class Comment(Base):
    """
    Content또는 Comment에 의존적인 댓글들.
    """

    __tablename__ = 'comments'

    created_at = Column(DateTime)
    id = Column(Integer, primary_key=True)
    uid = Column(Integer)
    data = Column(String)
    
    cid = Column(Integer, ForeignKey('contents.id'))
    content = relationship('Content', back_populates='comments')

    parent_id = Column(Integer, ForeignKey('comments.id'))
    children = relationship('Comment', lazy='joined')

    def to_json(self):
        return {
            'data': self.data
        }

