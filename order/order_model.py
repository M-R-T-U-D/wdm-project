from sqlalchemy import Column, Integer, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import declarative_base

Base = declarative_base()


class OrderItem(Base):
    """The Account class corresponds to the "accounts" database table.
    """
    __tablename__ = 'orderitems'

    id = Column(Integer, primary_key=True)
    user_id = Column(UUID(as_uuid=True), nullable=False)
    order_id = Column(UUID(as_uuid=True), nullable=False)
    item_id = Column(UUID(as_uuid=True), nullable=False)

class UserOrder(Base):
    """The Account class corresponds to the "accounts" database table.
    """
    __tablename__ = 'userorders'

    id = Column(Integer, primary_key=True)
    user_id = Column(UUID(as_uuid=True), nullable=False)
    order_id = Column(UUID(as_uuid=True), nullable=False)
