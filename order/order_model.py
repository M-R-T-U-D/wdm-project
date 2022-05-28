from sqlalchemy import Column, Integer, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import declarative_base

Base = declarative_base()


class Order(Base):
    """The Account class corresponds to the "accounts" database table.
    """
    __tablename__ = 'orders'

    id = Column(Integer, primary_key=True)
    order_id = Column(UUID(as_uuid=True), nullable=False)
    user_id = Column(UUID(as_uuid=True), nullable=False)

class Item(Base):
    """The Account class corresponds to the "accounts" database table.
    """
    __tablename__ = 'items'

    id = Column(Integer, primary_key=True)
    order_id = Column(UUID(as_uuid=True), nullable=False)
    item_id = Column(UUID(as_uuid=True), nullable=False)
