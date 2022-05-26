from sqlalchemy import Column, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import declarative_base

Base = declarative_base()


class Order(Base):
    """The Account class corresponds to the "accounts" database table.
    """
    __tablename__ = 'orders'

    id = Column(UUID(as_uuid=True), primary_key=True)
    user_id = Column(Text, nullable=False)
    order_id = Column(Text, nullable=False)
    item_id = Column(Text, nullable=False)