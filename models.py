from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, String, Integer

import db


Base = declarative_base(bind=db.engine)


class Content(Base):

    __tablename__ = 'contents'

    id = Column(Integer, primary_key=True)
    title = Column(String)
    data = Column(String)
