from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, String, Integer, DateTime, Enum, ARRAY, ForeignKey, Index
from sqlalchemy.orm import relationship

from datetime import datetime, timedelta

from db import Base

import enums


class ShowedContent(Base):

    __tablename__ = 'showed_contents'

    cid = Column(Integer, ForeignKey('contents.id'))
    content = relationship('Content', back_populates='showed_contents')

    uid = Column(Integer)
    
    __table_args__ = (Index('ix_uid_cid', "id", "cid"), )
 
    def to_json(self):
        date = self.created_at.strftime('%Y.%m.%d')

        now = datetime.utcnow() + timedelta(hours=9)
        delta = now - self.created_at
        if delta < timedelta(minutes=1):
            date = f'{int(delta.seconds)}초 전'
        elif delta < timedelta(hours=1):
            date = f'{int(delta.seconds//60)}분 전'
        elif delta < timedelta(days=1):
            date = f'{int(delta.seconds/60//60)}시간 전'
        elif delta < timedelta(days=7):
            date = f'{delta.days}일 전'

        return {
            'created_at': self.created_at,
            'date': date,
            'content': self.content.to_json()
        }
