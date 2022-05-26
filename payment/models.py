from sqlalchemy import Column, Text, Integer, Boolean
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import declarative_base

Base = declarative_base()


class Payment(Base):
    """The Account class corresponds to the "accounts" database table.
    """
    __tablename__ = 'payments'

    id = Column(Integer, primary_key=True)
    user_id = Column(UUID(as_uuid=True), nullable=False)
    order_id = Column(UUID(as_uuid=True), nullable=False)
    amount = Column(Integer, nullable=False)
    paid = Column(Boolean, nullable=False, default=False)

class User(Base):
    """The Account class corresponds to the "accounts" database table.
    """
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True)
    user_id = Column(UUID(as_uuid=True), nullable=False)
    credit = Column(Integer, nullable=False, default=0)