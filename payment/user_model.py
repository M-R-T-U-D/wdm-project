from sqlalchemy import Column, Text, Integer
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import declarative_base

Base = declarative_base()


class User(Base):
    """The Account class corresponds to the "accounts" database table.
    """
    __tablename__ = 'users'

    id = Column(UUID(as_uuid=True), primary_key=True)
    user_id = Column(Text, nullable=False)
    credit = Column(Integer, nullable=False, default=0)