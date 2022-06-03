import os
import sys
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy_cockroachdb import run_transaction
from sqlalchemy.orm.exc import NoResultFound, MultipleResultsFound
import uuid
from werkzeug.exceptions import HTTPException

from flask import Flask, jsonify

# NOTE: make sure to run this app.py from this folder, so python app.py so that models are also read correctly from root
sys.path.append("../")
from orm_models.models import Stock, Base

app = Flask("stock-service")

# TODO: Read db url from env variable instead of hardcoding here 
DATABASE_URL= "cockroachdb://root@localhost:26257/defaultdb?sslmode=disable"

try:
    engine = create_engine(DATABASE_URL, echo=True)
except Exception as e:
    print("Failed to connect to database.")
    print(f"{e}")

# Catch all unhandled exceptions
@app.errorhandler(Exception)
def handle_exception(e):
    # pass through HTTP errors
    if isinstance(e, HTTPException):
        return jsonify(error=str(e)), 400
    
    # now you're handling non-HTTP exceptions only
    return jsonify(error=str(e)), 400

class NotEnoughStockException(Exception):
    """Exception class for handling insufficient stock of an item"""
    def __str__(self) -> str:
         return "Stock cannot be negative"




@app.post('/item/create/<int:price>')
def create_item(price: int):
    item_uuid = uuid.uuid4()
    new_item = Stock(item_id=item_uuid, price=price)
    run_transaction(sessionmaker(bind=engine), lambda s: s.add(new_item))
    return jsonify(item_id=item_uuid)

def find_item_helper(session, item_id):
    item = session.query(Stock).filter(Stock.item_id == item_id).one()
    return item


@app.get('/find/<item_id>')
def find_item(item_id: str):
    try:
        ret_item = run_transaction(
            sessionmaker(bind=engine, expire_on_commit=False),
            lambda s: find_item_helper(s, item_id)
        )
        return jsonify(
            stock=ret_item.stock,
            price=ret_item.price
        )
    except NoResultFound:
        return "No item was found", 400
    except MultipleResultsFound:
        return "Multiple items were found while one is expected", 400

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
        return '', 200
    except NoResultFound:
        return "No item was found", 400
    except MultipleResultsFound:
        return "Multiple items were found while one is expected", 400

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
        return '', 200
    except NoResultFound:
        return "No item was found", 400
    except MultipleResultsFound:
        return "Multiple items were found while one is expected", 400
    except NotEnoughStockException as e:
        return str(e), 400

# TODO: delete main when testing is finalized
def main():
    Base.metadata.create_all(bind=engine, checkfirst=True)
    app.run(host="0.0.0.0", port=8081, debug=True)

if __name__ == '__main__':
    main()