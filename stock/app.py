from lib2to3.pgen2.token import AMPER
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy_cockroachdb import run_transaction
from sqlalchemy.orm.exc import NoResultFound, MultipleResultsFound
import uuid

from flask import Flask, jsonify

from stock.stock_model import Stock

app = Flask("stock-service")

DATABASE_URL= "cockroachdb://root@localhost:26257/defaultdb?sslmode=disable"

try:
    engine = create_engine(DATABASE_URL, echo=True)
except Exception as e:
    print("Failed to connect to database.")
    print(f"{e}")

class NotEnoughStockException(Exception):
    """Exception class for handling insufficient stock of an item"""
    def __str__(self) -> str:
         return "Not enough stock"

@app.post('/item/create/<int:price>')
def create_item(price: int):
    item_uuid = uuid.uuid4()
    new_item = Stock(item_id=item_uuid, price=price)
    run_transaction(sessionmaker(bind=engine), lambda s: s.add(new_item))
    return jsonify(user_id=item_uuid)

def find_item_helper(session, item_id):
    try:
        item = session.query(Stock).filter(Stock.item_id == item_id).one()
        return item
    except NoResultFound:
        print("No item was found")
    except MultipleResultsFound:
        print("Multiple items were found while one is expected")
    return None

@app.get('/find/<item_id>')
def find_item(item_id: str):
    ret_item = run_transaction(
        sessionmaker(bind=engine, expire_on_commit=False),
        lambda s: find_item_helper(s, item_id)
    )
    if ret_item:
        return jsonify(ret_item.stock, ret_item.price)
    else:
        return '', 400

def add_stock_helper(session, item_id, amount):
    item = session.query(Stock).filter(Stock.item_id == item_id).one()
    item.stock += amount

@app.post('/add/<item_id>/<int:amount>')
def add_stock(item_id: str, amount: int):
    try:
        run_transaction(
            sessionmaker(bind=engine),
            lambda s: add_stock_helper(s, item_id, amount)
        )
        return jsonify(done=True)
    except NoResultFound:
        print("No item was found")
    except MultipleResultsFound:
        print("Multiple items were found while one is expected")

def remove_stock_helper(session, item_id, amount):
    item = session.query(Stock).filter(Stock.item_id == item_id).one()
    if item.stock >= amount:
        item.stock -= amount
    else:
        raise NotEnoughStockException()

@app.post('/subtract/<item_id>/<int:amount>')
def remove_stock(item_id: str, amount: int):
    try:
        run_transaction(
            sessionmaker(bind=engine),
            lambda s: remove_stock_helper(s, item_id, amount)
        )
    except NoResultFound:
        return "No item was found", 400
    except MultipleResultsFound:
        return "Multiple items were found while one is expected", 400
    except NotEnoughStockException as e:
        return str(e), 400
