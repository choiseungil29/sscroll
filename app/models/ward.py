from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, String, Integer, DateTime, Enum, ARRAY, ForeignKey
from sqlalchemy.orm import relationship

from datetime import datetime

from db import Base

import enums


class Ward(Base):
    """
    와드 컨텐츠.
    """

    __tablename__ = 'wards'

    id = Column(Integer, primary_key=True)

    created_at = Column(DateTime, default=datetime.now)
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


