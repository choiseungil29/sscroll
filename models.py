from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, String, Integer, DateTime

import db



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
    origin = Column(String)
    created_at = Column(DateTime)

    def header(self):
        pass

    def body(self):
        pass

    def content(self):
        pass

    def to_html(self):
        pass

