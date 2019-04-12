import enums

from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, String, Integer, DateTime, Enum, ARRAY, ForeignKey
from sqlalchemy.orm import relationship

from db import Base



class User(Base):
    """
    유저
    """

    __tablename__ = 'users'

    nickname = Column(String)

    def to_json(self):
        return {
            'nickname': self.nickname
        }

