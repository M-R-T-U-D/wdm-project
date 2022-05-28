from sqlalchemy import Column, Text, Integer, Boolean, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import declarative_base

Base = declarative_base()


class Payment(Base):
    """The Payment class corresponds to the "payments" database table.
    """
    __tablename__ = 'payments'

    id = Column(Integer, primary_key=True)
    user_id = Column(UUID(as_uuid=True), nullable=False)
    order_id = Column(UUID(as_uuid=True), nullable=False)
    amount = Column(Integer, nullable=False)
    paid = Column(Boolean, nullable=False, default=False)

    def to_dict(self):
       return {c.name: getattr(self, c.name) for c in self.__table__.columns}

class User(Base):
    """The User class corresponds to the "users" database table.
    """
    __tablename__ = 'users'

    user_id = Column(UUID(as_uuid=True), primary_key=True)
    credit = Column(Integer, nullable=False, default=0)

    def to_dict(self):
       return {c.name: getattr(self, c.name) for c in self.__table__.columns}