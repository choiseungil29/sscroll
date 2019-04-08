from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, String, Integer, DateTime, Enum, ARRAY, ForeignKey
from sqlalchemy.orm import relationship

import db
from db import Base

from app import models


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
    session = db.session.object_session(self)
    user = session.query(models.User).\
      filter(models.User.id == self.uid).\
      first()

    return {
      'data': self.data,
      'id': self.id,
      'parent_id': self.parent_id,
      'children': [c.to_json() for c in self.children],
      'user': user.to_json(),
      'created_at': self.created_at,
      'date': self.created_at.strftime('%Y.%m.%d'),
      'content_pid': self.content.permanent_id
    }
