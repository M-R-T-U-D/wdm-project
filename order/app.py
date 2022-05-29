import os
import sys
from pyparsing import Or
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy_cockroachdb import run_transaction
from sqlalchemy.orm.exc import NoResultFound, MultipleResultsFound
import uuid

import requests
from flask import Flask, jsonify

# NOTE: make sure to run this app.py from this folder, so python app.py so that models are also read correctly from root
sys.path.append("../")
from orm_models.models import Order, Cart


gateway_url = os.environ['GATEWAY_URL']

app = Flask("order-service")

DATABASE_URL= "cockroachdb://root@localhost:26257/defaultdb?sslmode=disable"

try:
    engine = create_engine(DATABASE_URL, echo=True)
except Exception as e:
    print("Failed to connect to database.")
    print(f"{e}")


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
            sessionmaker(bind=engine, expire_on_commit=False),
            lambda s: remove_order_helper(s, order_id)
        )
    except NoResultFound:
        return "No order was found", 400

def find_user_order_helper(session, order_id):
    try:
        user_order = session.query(Order).filter(Order.order_id == order_id).one()
        return user_order
    except NoResultFound:
        print("No user_order was found")
    except MultipleResultsFound:
        print("Multiple user_orders were found while one is expected")
    return None

@app.post('/addItem/<order_id>/<item_id>')
def add_item(order_id, item_id):
    ret_user_order = run_transaction(
        sessionmaker(bind=engine, expire_on_commit=False),
        lambda s: find_user_order_helper(s, order_id)
    )
    if ret_user_order:
        user_order_dict = ret_user_order.as_dict()
        user_order_dict.pop('id') # remove id from the user dict
        new_order = Cart(user_order_dict.user_id, order_id, item_id)
        run_transaction(sessionmaker(bind=engine), lambda s: s.add(new_order))
        return '',200
    else:
        return '',400

def remove_order_item_helper(session, order_id, item_id):
    session.query(Cart).filter(Cart.order_id == order_id and Cart.item_id == item_id).delete()

@app.delete('/removeItem/<order_id>/<item_id>')
def remove_item(order_id, item_id):
    try:
        run_transaction(
            sessionmaker(bind=engine, expire_on_commit=False),
            lambda s: remove_order_item_helper(s, order_id, item_id)
        )
    except NoResultFound:
        return "No order_item was found", 400

def find_order_items_helper(session, order_id):
    try:
        order_items = session.query(Order).filter(Order.order_id == order_id).all()
        return order_items
    except NoResultFound:
        print("No order_items were found")
    return None
 
@app.get('/find/<order_id>')
def find_order(order_id):
    ret_user_order = run_transaction(
        sessionmaker(bind=engine, expire_on_commit=False),
        lambda s: find_user_order_helper(s, order_id)
    )
    ret_order_items = run_transaction(
        sessionmaker(bind=engine, expire_on_commit=False),
        lambda s: find_order_items_helper(s, order_id)
    )

    if ret_user_order and ret_order_items:
        
        status = requests.post(f"http://localhost:8081/status/{ret_user_order.user_id}/{order_id}").json()['paid']
        items = []
        total_cost = 0
        for order_item in ret_order_items:
            stock_price = requests.get(f"http://localhost:8081/find/{order_item.item_id}").json()['price']
            total_cost += stock_price
            items.append(order_item.item_id)
        return jsonify(order_id=order_id, paid=status, items=items, user_id=ret_user_order.user_id, total_cost=total_cost)
    else:
        return '', 400



@app.post('/checkout/<order_id>')
def checkout(order_id):
    try:
        ret_order = find_order(order_id)
        print(requests.post(f"http://localhost:8081/pay/{ret_order['user_id']}/{ret_order['order_id']}/{ret_order['total_cost']}").status_code)
        for item_id in ret_order['items']:
            print(requests.post(f"http://localhost:8081/subtract/{item_id}/{1}").status_code)
        return 'success', 200
    except Exception:
        return 'failure', 400

