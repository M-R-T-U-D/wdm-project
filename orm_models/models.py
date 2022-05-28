from sqlalchemy import Column, Text, Integer, Boolean, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import declarative_base, relationship

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
    fk_user_order_id = relationship(
        "Order",
        cascade="all, delete", # if there are children present in the session as the User object, then mark all of them for deletion
        passive_deletes=True # defers the deletion of children to the database
    )

    def to_dict(self):
       return {c.name: getattr(self, c.name) for c in self.__table__.columns}

class Order(Base):
    """The Order class corresponds to the "orders" database table.
    """
    __tablename__ = 'orders'

    order_id = Column(UUID(as_uuid=True), primary_key=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.user_id', ondelete="CASCADE"))
    fk_order_item_id = relationship(
        "Cart",
        cascade="all, delete",
        passive_deletes=True
    )

    def to_dict(self):
       return {c.name: getattr(self, c.name) for c in self.__table__.columns}

class Cart(Base):
    """The Cart class corresponds to the "carts" database table.
    """
    __tablename__ = 'carts'

    id = Column(Integer, primary_key=True)
    item_id = Column(UUID(as_uuid=True), nullable=False)
    order_id = Column(UUID(as_uuid=True), ForeignKey('orders.order_id', ondelete="CASCADE"))

    def to_dict(self):
       return {c.name: getattr(self, c.name) for c in self.__table__.columns}

class Stock(Base):
    """The Stock class corresponds to the "stocks" database table.
    """
    __tablename__ = 'stocks'

    item_id = Column(UUID(as_uuid=True), primary_key=True)
    stock = Column(Integer, nullable=False, default=0)
    price = Column(Integer, nullable=False)