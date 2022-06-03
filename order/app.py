import os
import sys
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy_cockroachdb import run_transaction
from sqlalchemy.orm.exc import NoResultFound, MultipleResultsFound
from werkzeug.exceptions import HTTPException
import uuid

import json
import requests
from flask import Flask, jsonify

# NOTE: make sure to run this app.py from this folder, so python app.py so that models are also read correctly from root
sys.path.append("../")
from orm_models.models import Order, Cart, Base

app = Flask("order-service")

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





@app.post('/create/<user_id>')
def create_order(user_id):
    order_uuid = uuid.uuid4()
    new_user_order = Order(order_id=order_uuid, user_id=user_id)
    run_transaction(sessionmaker(bind=engine), lambda s: s.add(new_user_order))
    return jsonify(order_id=order_uuid)

def remove_order_helper(session, order_id):
    session.query(Order).filter(Order.order_id == order_id).delete()

@app.delete('/remove/<order_id>')
def remove_order(order_id):
    try:
        run_transaction(
            sessionmaker(bind=engine),
            lambda s: remove_order_helper(s, order_id)
        )
        return '', 200
    except Exception:
        return "Something went wrong", 400

def add_item_order_helper(session, order_id, item_id):
    new_item_order = Cart(item_id=item_id, order_id=order_id)
    session.add(new_item_order)

@app.post('/addItem/<order_id>/<item_id>')
def add_item(order_id, item_id):
    try:
        run_transaction(
            sessionmaker(bind=engine),
            lambda s: add_item_order_helper(s, order_id, item_id)
        )
        return '',200
    except NoResultFound:
        return "No user_order was found", 400
    except MultipleResultsFound:
        return "Multiple user_orders were found while one is expected", 400

def remove_order_item_helper(session, order_id, item_id):
    session.query(Cart).filter(Cart.order_id == order_id, Cart.item_id == item_id).delete()

@app.delete('/removeItem/<order_id>/<item_id>')
def remove_item(order_id, item_id):
    try:
        run_transaction(
            sessionmaker(bind=engine),
            lambda s: remove_order_item_helper(s, order_id, item_id)
        )
        return '', 200
    except Exception:
        return "Something went wrong!", 400

def find_order_items_helper(session, order_id):
    order_items = session.query(Cart).filter(Cart.order_id == order_id).all()
    return order_items

@app.get('/find/<order_id>')
def find_order(order_id):
    try:
        ret_user_order: Order = run_transaction(
            sessionmaker(bind=engine, expire_on_commit=False),
            lambda s: s.query(Order).filter(Order.order_id == order_id).one()
        )
        ret_order_items: list[Cart] = run_transaction(
            sessionmaker(bind=engine, expire_on_commit=False),
            lambda s: find_order_items_helper(s, order_id)
        )

        if ret_user_order and ret_order_items:
            status = requests.post(f"http://localhost:8083/status/{ret_user_order.user_id}/{order_id}").json()['paid']
            items = []
            total_cost = 0
            for order_item in ret_order_items:
                stock_price = requests.get(f"http://localhost:8081/find/{order_item.item_id}").json()['price']
                total_cost += stock_price
                items.append(order_item.item_id)
            return jsonify(
                order_id=order_id,
                paid=status, 
                items=items, 
                user_id=ret_user_order.user_id, 
                total_cost=total_cost
            ), 200
        else:
            return 'Something went wrong!', 400
    except NoResultFound:
        return "No user_order was found", 400
    except MultipleResultsFound:
        return "Multiple user_orders were found while one is expected", 400



@app.post('/checkout/<order_id>')
def checkout(order_id):
    try:
        
        ret_order = json.loads(find_order(order_id)[0].get_data(as_text=True))
        status_before = ret_order['paid']
        print(requests.post(f"http://localhost:8083/pay/{ret_order['user_id']}/{ret_order['order_id']}/{ret_order['total_cost']}").status_code)
        if not status_before:
            for item_id in ret_order['items']:
                print(requests.post(f"http://localhost:8081/subtract/{item_id}/1").status_code)
        return 'success', 200
    except Exception as e:
        print(e)
        return 'failure', 400

# TODO: delete main when testing is finalized
def main():
    Base.metadata.create_all(bind=engine, checkfirst=True)
    app.run(host="0.0.0.0", port=8082, debug=True)

if __name__ == '__main__':
    main()