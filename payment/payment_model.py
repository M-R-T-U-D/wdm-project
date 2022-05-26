from sqlalchemy import Column, Text, Integer, Boolean
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import declarative_base

Base = declarative_base()


class Payment(Base):
    """The Account class corresponds to the "accounts" database table.
    """
    __tablename__ = 'payments'

    id = Column(UUID(as_uuid=True), primary_key=True)
    user_id = Column(Text)
    order_id = Column(Text)
    amount = Column(Integer)
    paid = Column(Integer)