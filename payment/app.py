import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy_cockroachdb import run_transaction
from sqlalchemy.orm.exc import NoResultFound, MultipleResultsFound
import uuid

from flask import Flask, jsonify
from models import Payment, User, Base

app = Flask("payment-service")

DATABASE_URL= "cockroachdb://root@localhost:26257/defaultdb?sslmode=disable"

try:
    engine = create_engine(DATABASE_URL, echo=True)
except Exception as e:
    print("Failed to connect to database.")
    print(f"{e}")

class NotEnoughCreditException(Exception):
    """Exception class for handling insufficient credits of a user"""
    def __str__(self) -> str:
         return "Not enough credits"

@app.post('/create_user')
def create_user():
    user_uuid = uuid.uuid4()
    new_user = User(user_id=user_uuid)
    run_transaction(sessionmaker(bind=engine), lambda s: s.add(new_user))
    return jsonify(user_id=user_uuid)

def find_user_helper(session, user_id):
    try:
        user = session.query(User).filter(User.user_id == user_id).one()
        return user
    except NoResultFound:
        print("No user was found")
    except MultipleResultsFound:
        print("Multiple users were found while one is expected")
    return None

@app.get('/find_user/<user_id>')
def find_user(user_id: str):
    # expire_on_commit=False to reuse returned User object attrs
    ret_user = run_transaction(
        sessionmaker(bind=engine, expire_on_commit=False),
        lambda s: find_user_helper(s, user_id)
    )
    if ret_user:
        user_dict = ret_user.as_dict()
        user_dict.pop('id') # remove id from the user dict
        return jsonify(user_dict)
    else:
        return '',400

def add_credit_helper(session, user_id, amount):
    user = session.query(User).filter(User.user_id == user_id).one()
    user.credit += amount

@app.post('/add_funds/<user_id>/<int:amount>')
def add_credit(user_id: str, amount: int):
    try:
        run_transaction(
            sessionmaker(bind=engine),
            lambda s: add_credit_helper(s, user_id, amount)
        )
        return jsonify(done=True)
    except NoResultFound:
        print("No user was found")
    except MultipleResultsFound:
        print("Multiple users were found while one is expected")
    return jsonify(done=False)

def remove_credit_helper(session, user_id, order_id, amount):
    user = session.query(User).filter(User.user_id == user_id).one()
    new_payment = Payment(user_id=user_id, order_id=order_id, amount=amount)
    if (user.credit >= amount):
        user.credit -= amount
        new_payment.paid = True
    else:
        raise NotEnoughCreditException()
    session.add(new_payment)
    
@app.post('/pay/<user_id>/<order_id>/<int:amount>')
def remove_credit(user_id: str, order_id: str, amount: int):
    try:
        run_transaction(
            sessionmaker(bind=engine),
            lambda s: remove_credit_helper(s, user_id, order_id, amount)
        )
    except NoResultFound:
        return "No user or payment was found", 400
    except MultipleResultsFound:
        return "Multiple users or payments were found while one is expected", 400
    except NotEnoughCreditException as e:
        return str(e), 400

def cancel_payment_helper(session, user_id, order_id):
    user = session.query(User).filter(User.user_id == user_id).one()
    payment = session.query(Payment).filter(Payment.user_id == user_id and Payment.order_id == order_id).one()
    user.credit += payment.amount
    payment.paid = False
    
@app.post('/cancel/<user_id>/<order_id>')
def cancel_payment(user_id: str, order_id: str):
    try:
        run_transaction(
            sessionmaker(bind=engine), 
            lambda s: cancel_payment_helper(s, user_id, order_id)
        )
    except NoResultFound:
        return "No user or payment was found", 400
    except MultipleResultsFound:
        return "Multiple users or payments were found while one is expected", 400


def status_helper(session, user_id, order_id):
    payment = session \
        .query(Payment) \
        .filter(
            Payment.user_id == user_id 
            and
            Payment.order_id == order_id
        ).one()
    return payment.paid

@app.post('/status/<user_id>/<order_id>')
def payment_status(user_id: str, order_id: str):
    try:
        ret_paid = run_transaction(
            sessionmaker(bind=engine), 
            lambda s: status_helper(s, user_id, order_id)
        )
        return jsonify(paid=ret_paid)
    except NoResultFound:
        return "No payment was found", 400
    except MultipleResultsFound:
        return "Multiple payments were found while one is expected", 400


# TODO: delete main when testing is finalized
def main():
    Base.metadata.create_all(bind=engine, checkfirst=True)
    app.run(host="0.0.0.0", port=8081, debug=True)

if __name__ == '__main__':
    main()