import os
import sys
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy_cockroachdb import run_transaction
from sqlalchemy.orm.exc import NoResultFound, MultipleResultsFound
from werkzeug.exceptions import HTTPException
import uuid

import json
from flask import Flask, jsonify

# NOTE: make sure to run this app.py from this folder, so python app.py so that models are also read correctly from root
sys.path.append("../")
from orm_models.models import Order, Cart, Payment, Stock, User

stock_url = os.environ['STOCK_URL']
payment_url = os.environ['PAYMENT_URL']
datebase_url = os.environ['DATABASE_URL']

app = Flask("order-service")

try:
    engine = create_engine(datebase_url)
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


class NotEnoughCreditException(Exception):
    """Exception class for handling insufficient credits of a user"""

    def __str__(self) -> str:
        return "Not enough credits"


class NotEnoughStockException(Exception):
    """Exception class for handling insufficient stock of an item"""

    def __str__(self) -> str:
        return "Stock cannot be negative"


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
        return '', 200
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


def payment_status_helper(session, user_id, order_id):
    payment_paid = session \
        .query(Payment) \
        .filter(
        Payment.user_id == user_id,  # and
        Payment.order_id == order_id
    ).first()
    return payment_paid

def payment_status(user_id: str, order_id: str):
    try:
        ret_paid = run_transaction(
            sessionmaker(bind=engine, expire_on_commit=False),
            lambda s: payment_status_helper(s, user_id, order_id)
        )
        if ret_paid:
            return jsonify(paid=True), 200
        else:
            return jsonify(paid=False), 200
    except MultipleResultsFound:
        return "Multiple payments were found while one or zero is expected", 400
    except Exception as e:
        return str(e), 404


def find_item_stock_helper(session, item_id):
    item = session.query(Stock).filter(Stock.item_id == item_id).one()
    return item


def find_item_stock(item_id: str):
    try:
        ret_item = run_transaction(
            sessionmaker(bind=engine, expire_on_commit=False),
            lambda s: find_item_stock_helper(s, item_id)
        )
        return jsonify(
            stock=ret_item.stock,
            price=ret_item.price
        ), 200
    except NoResultFound:
        return "No item was found", 400
    except MultipleResultsFound:
        return "Multiple items were found while one is expected", 400


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
            pay_status = payment_status(ret_user_order.user_id, order_id)
            if pay_status[1] >= 400:
                return pay_status
            status = pay_status[0].json['paid']
            items = []
            total_cost = 0.0
            for order_item in ret_order_items:
                stock_price = find_item_stock(order_item.item_id)
                if (stock_price[1] >= 400):
                    return stock_price
                stock_price = json.loads(stock_price[0].get_data(as_text=True))['price']
                total_cost += float(stock_price)
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


def pay_credit_helper(session, user_id, order_id, amount):
    user = session.query(User).filter(User.user_id == user_id).one()

    status = json.loads(payment_status(user_id, order_id).get_data(as_text=True))
    if not status['paid']:
        if user.credit >= amount:
            user.credit -= amount
            new_payment = Payment(user_id=user_id, order_id=order_id, amount=amount)
            session.add(new_payment)
        else:
            raise NotEnoughCreditException()

def pay_credit(user_id: str, order_id: str, amount: float):
    try:
        run_transaction(
            sessionmaker(bind=engine),
            lambda s: pay_credit_helper(s, user_id, order_id, float(amount))
        )
        return '', 200
    except NoResultFound:
        return "No user or order was found", 401
    except MultipleResultsFound:
        return "Multiple users or order were found while one is expected", 402
    except NotEnoughCreditException as e:
        return str(e), 403
    except Exception as e:
        return str(e), 404


def remove_stock_helper(session, item_id, amount):
    item = session.query(Stock).filter(Stock.item_id == item_id).one()
    if item.stock >= amount:
        item.stock -= amount
    else:
        raise NotEnoughStockException()

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


@app.post('/checkout/<order_id>')
def checkout(order_id):
    try:
        ord = find_order(order_id)
        if ord[1] >= 400:
            return ord
        ret_order = json.loads(ord[0].get_data(as_text=True))
        status_before = ret_order['paid']
        resp_pay = pay_credit(ret_order['user_id'], ret_order['order_id'], ret_order['total_cost'])
        print(f'{resp_pay[1]=}')
        if resp_pay[1] >= 400:
            return resp_pay
        if not status_before:
            for item_id in ret_order['items']:
                resp_stock = remove_stock(item_id, 1)
                print(f'{resp_stock[1]=}')
                if resp_stock[1] >= 400:
                    return resp_stock

        return 'success', 200
    except Exception as e:
        return str(e), 400
