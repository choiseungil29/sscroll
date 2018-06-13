from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, String, Integer, DateTime, Enum

import db
import enums


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
    source = Column(Enum(enums.DataOriginEnum))
    created_at = Column(DateTime)

    def header(self):
        pass

    def body(self):
        pass

    def content(self):
        pass

    def to_html(self):
        pass


class User(Base):
    """
    유저
    """

    __tablename__ = 'users'

    id = Column(Integer, primary_key=True)
    signup_type = Column(Enum(enums.SignupTypeEnum))
    email = Column(String)
