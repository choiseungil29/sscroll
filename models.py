from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, String, Integer, DateTime, Enum, ARRAY, ForeignKey
from sqlalchemy.orm import relationship

import db
import enums
import datetime


Base = declarative_base(bind=db.engine)


class Content(Base):
    """
    모든 컨텐츠.
    """

    __tablename__ = 'contents'

    id = Column(Integer, primary_key=True)
    title = Column(String)
    data = Column(String)
    permanent_id = Column(String, unique=True, index=True)
    origin = Column(Enum(enums.DataOriginEnum))
    created_at = Column(DateTime)
    showed_contents = relationship('ShowedContent', back_populates='content', order_by='ShowedContent.created_at')
    comments = relationship('Comment', back_populates='content')


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


class User(Base):
    """
    유저
    """

    __tablename__ = 'users'

    id = Column(Integer, primary_key=True)
    signup_type = Column(Enum(enums.SignupTypeEnum))
    email = Column(String)
    access_token = Column(String) # signup_type을 따라가는 token.


class Ward(Base):
    """
    와드 컨텐츠.
    """

    __tablename__ = 'wards'

    id = Column(Integer, primary_key=True)

    created_at = Column(DateTime, default=datetime.datetime.now)
    uid = Column(Integer, index=True)
    cid = Column(Integer, ForeignKey('contents.id'))
    content = relationship('Content')


    def to_json(self):

        data = {}
        if self.id is not None:
            data['id'] = self.id

        if self.created_at is not None:
            data['created_at'] = self.created_at

        if self.uid is not None:
            data['uid'] = self.uid

        if self.cid is not None:
            data['cid'] = self.cid

        return data

    def from_json(self):
        pass


class ShowedContent(Base):

    __tablename__ = 'showed_contents'

    id = Column(Integer, primary_key=True)
    cid = Column(Integer, ForeignKey('contents.id'))
    content = relationship('Content', back_populates='showed_contents')

    uid = Column(Integer)
    
    created_at = Column(DateTime, default=datetime.datetime.now)
    
