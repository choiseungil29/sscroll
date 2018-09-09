from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, String, Integer, DateTime, Enum, ARRAY, ForeignKey
from sqlalchemy.orm import relationship

from datetime import datetime

from db import Base

import enums


class ShowedContent(Base):

    __tablename__ = 'showed_contents'

    id = Column(Integer, primary_key=True)
    cid = Column(Integer, ForeignKey('contents.id'))
    content = relationship('Content', back_populates='showed_contents')

    uid = Column(Integer)
    
    created_at = Column(DateTime, default=datetime.now)
 
