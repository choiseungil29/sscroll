from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, String, Integer, DateTime, Enum, ARRAY, ForeignKey, Table
from sqlalchemy.orm import relationship, backref

from datetime import datetime, timedelta

from app import models
from db import Base

import db
import enums


class Content(Base):
    """
    모든 컨텐츠.
    """

    __tablename__ = 'contents'

    uid = Column(Integer)
    title = Column(String)
    data = Column(String)
    permanent_id = Column(String, unique=True, index=True)
    origin = Column(Enum(enums.DataOriginEnum))
    showed_contents = relationship('ShowedContent', back_populates='content', order_by='ShowedContent.created_at')
    comments = relationship('Comment', back_populates='content')

    up = Column(Integer, default=0)
    down = Column(Integer, default=0)
    ups = relationship('User', secondary='likes_with_users')
    downs = relationship('User', secondary='unlikes_with_users')

    def to_json(self):
        user = self.session.query(models.User).\
            filter(models.User.id == self.uid).\
            first()
        
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
        
        print(self.title)
        if '0.0' in date:
            breakpoint()
            print('sibal')
        print(date)
        # breakpoint()

        return {
            'id': self.id,
            'title': self.title,
            'data': self.data,
            'permanent_id': self.permanent_id,
            'created_at': self.created_at,
            # 'comments': [c.to_json() for c in self.comments],
            'comments': [],
            'up': self.up,
            'ups': [u.to_json() for u in self.ups],
            'down': self.down,
            'downs': [u.to_json() for u in self.downs],
            'date': date,
            'user': user.to_json(),
            'type': self.origin
        }


LikesWithUsers = Table('likes_with_users', Base.metadata,
    Column('content_id', Integer, ForeignKey('contents.id')),
    Column('user_id', Integer, ForeignKey('users.id')))

UnlikesWithUsers = Table('unlikes_with_users', Base.metadata,
    Column('content_id', Integer, ForeignKey('contents.id')),
    Column('user_id', Integer, ForeignKey('users.id')))