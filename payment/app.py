import imp
import os
import atexit
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy_cockroachdb import run_transaction
from sqlalchemy.orm.exc import NoResultFound, MultipleResultsFound
import uuid

from flask import Flask, jsonify
from payment_model import Payment
from user_model import User

app = Flask("payment-service")

DATABASE_URL= "postgresql://127.0.0.1:26257?sslmode=disable"

try:
    engine = create_engine(DATABASE_URL)
except Exception as e:
        print("Failed to connect to database.")
        print(f"{e}")

@app.post('/create_user')
def create_user():
    user_uuid = uuid.uuid4()
    new_user = User(user_id=user_uuid)
    run_transaction(sessionmaker(bind=engine), lambda s: s.add(new_user))
    return jsonify(user_id=user_uuid)

def find_user_helper(session, user_id):
    try:
        user = session.query(User).filter(User.user_id == user_id).one()
    except NoResultFound:
            print("No user was found")
    except MultipleResultsFound:
            print("Multiple users were found while one is expected")
    return jsonify(user_id=user.user_id, credit=user.credit)

@app.get('/find_user/<user_id>')
def find_user(user_id: str):
    # try:
    #     user = session.query(User).filter(User.user_id == user_id).one()
    # except NoResultFound:
    #         print("No user was found")
    # except MultipleResultsFound:
    #         print("Multiple users were found while one is expected")
    # run_transaction(sessionmaker(bind=engine), lambda s: find_user_helper(s, user_id))
    # return jsonify(user_id=user.user_id, credit=user.credit)
    pass

def add_credit_helper(session, user_id, amount):
    try:
        user = session.query(User).filter(User.user_id == user_id).one()
    except NoResultFound:
            print("No user was found")
    except MultipleResultsFound:
            print("Multiple users were found while one is expected")
    user.credit += amount

@app.post('/add_funds/<user_id>/<amount>')
def add_credit(user_id: str, amount: int):
    try:
        run_transaction(sessionmaker(bind=engine), lambda s: add_credit_helper(s, user_id, amount))
        return jsonify(done=True)
    except Exception as e:
        print(e)
        return jsonify(done=False)

def remove_credit_helper(session, user_id, order_id, amount):
    try:
        user = session.query(User).filter(User.user_id == user_id).one()
        new_payment = Payment(user_id=user_id, order_id=order_id, amount=amount)
        if (user.credit >= amount):
            user.credit -= amount
            new_payment.paid = True
        session.add(new_payment)
    except NoResultFound:
            print("No user was found")
    except MultipleResultsFound:
            print("Multiple users were found while one is expected")

@app.post('/pay/<user_id>/<order_id>/<amount>')
def remove_credit(user_id: str, order_id: str, amount: int):
    try:
        run_transaction(sessionmaker(bind=engine), lambda s: remove_credit_helper(s, user_id, order_id, amount))
    except Exception as e:
        print(e)

def cancel_payment_helper(session, user_id, order_id):
    try:
        user = session.query(User).filter(User.user_id == user_id).one()
        payment = session.query(Payment).filter(Payment.user_id == user_id and Payment.order_id == order_id).one()
        user.credit += payment.amount
        payment.paid = False
    except NoResultFound:
            print("No user or payment was found")
    except MultipleResultsFound:
            print("Multiple users or payments were found while one is expected")

@app.post('/cancel/<user_id>/<order_id>')
def cancel_payment(user_id: str, order_id: str):
    try:
        run_transaction(sessionmaker(bind=engine), lambda s: cancel_payment_helper(s, user_id, order_id))
    except Exception as e:
        print(e)

def status_helper(session, user_id, order_id):
    try:
        payment = session.query(Payment).filter(Payment.user_id == user_id and Payment.order_id == order_id).one()
        return payment.paid
    except NoResultFound:
            print("No payment was found")
            return False
    except MultipleResultsFound:
            print("Multiple payments were found while one is expected")
            return False

@app.post('/status/<user_id>/<order_id>')
def payment_status(user_id: str, order_id: str):
    try:
        run_transaction(sessionmaker(bind=engine), lambda s: status_helper(s, user_id, order_id))
    except Exception as e:
        print(e)
