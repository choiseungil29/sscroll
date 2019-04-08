from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, String, Integer, DateTime, Enum, ARRAY, ForeignKey
from sqlalchemy.orm import relationship

from datetime import datetime

from app import models
from db import Base

import db
import enums


class Content(Base):
    """
    모든 컨텐츠.
    """

    __tablename__ = 'contents'

    id = Column(Integer, primary_key=True)
    uid = Column(Integer)
    title = Column(String)
    data = Column(String)
    permanent_id = Column(String, unique=True, index=True)
    origin = Column(Enum(enums.DataOriginEnum))
    created_at = Column(DateTime)
    showed_contents = relationship('ShowedContent', back_populates='content', order_by='ShowedContent.created_at')
    comments = relationship('Comment', back_populates='content')

    up = Column(Integer)
    down = Column(Integer)

    def to_json(self):
        session = db.session.object_session(self)
        user = session.query(models.User).\
            filter(models.User.id == self.uid).\
            first()

        return {
            'title': self.title,
            'data': self.data,
            'permanent_id': self.permanent_id,
            'created_at': self.created_at,
            'comments': [c.to_json() for c in self.comments],
            'up': self.up,
            'down': self.down,
            'date': self.created_at.strftime('%Y.%m.%d'),
            'user': user.to_json()
        }
    
    def is_view(self):
        pass

