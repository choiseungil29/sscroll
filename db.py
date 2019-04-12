from sqlalchemy import create_engine, Column, DateTime, Integer
from sqlalchemy.orm import scoped_session, sessionmaker
from sqlalchemy.ext.declarative import declarative_base

from datetime import datetime
from config import Config

engine = create_engine(f'postgresql+psycopg2://{Config.DB_USERNAME}:{Config.DB_PASSWORD}@{Config.DB_HOST}:{Config.DB_PORT}/{Config.DB_NAME}', pool_size=50, max_overflow=0)
session = scoped_session(sessionmaker(autocommit=False, autoflush=False, bind=engine))


class Base:
  id = Column(Integer, primary_key=True)

  created_at = Column(DateTime, default=datetime.now)
  updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)


  @property
  def session(self):
    return session.object_session(self)
    

  '''def to_json(self):
    # TODO: 자신의 column들을 탐색해 전부 JSON으로 변환 및 반환
    data = {}
    for column in self.__table__.columns:
      attr = getattr(self, column.key)
      print(type(attr))
      if type(attr) is datetime:
        attr = int(attr.timestamp() * 1000)
      data[column.key] = attr

    return data'''

Base = declarative_base(bind=engine, cls=Base)