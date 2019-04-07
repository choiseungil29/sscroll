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

    id = Column(Integer, primary_key=True)
    # signup_type = Column(Enum(enums.SignupTypeEnum))
    nickname = Column(String)
    # email = Column(String)
    # access_token = Column(String) # signup_type을 따라가는 token.

    def to_json(self):
        return {
            'nickname': self.nickname
        }

