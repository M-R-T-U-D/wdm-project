from sqlalchemy import Column, Text, Integer
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import declarative_base

Base = declarative_base()

class Stock(Base):
    """The Account class corresponds to the "accounts" database table.
    """
    __tablename__ = 'stocks'

    id = Column(Integer, primary_key=True)
    item_id = Column(UUID(as_uuid=True), nullable=False)
    stock = Column(Integer, nullable=False, default=0)
    price = Column(Integer, nullable=False)