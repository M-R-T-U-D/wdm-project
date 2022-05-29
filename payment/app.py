import os
import sys
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy_cockroachdb import run_transaction
from sqlalchemy.orm.exc import NoResultFound, MultipleResultsFound
from werkzeug.exceptions import HTTPException
import uuid

from flask import Flask, jsonify

# NOTE: make sure to run this app.py from this folder, so python app.py so that models are also read correctly from root
sys.path.append("../")
from orm_models.models import Order, Payment, User, Cart, Base 

app = Flask("payment-service")

DATABASE_URL= "cockroachdb://root@localhost:26257/defaultdb?sslmode=disable"

# Create engine to connect to the database
try:
    engine = create_engine(DATABASE_URL, echo=True)
except Exception as e:
    print("Failed to connect to database.")
    print(f"{e}")

# @app.errorhandler(HTTPException)
# def handle_http_exception(e: HTTPException):
#     """Return JSON for HTTP errors."""
#     print(e.get_response())
#     return jsonify(error=400)

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




@app.post('/create_user')
def create_user():
    user_uuid = uuid.uuid4()
    new_user = User(user_id=user_uuid)
    run_transaction(sessionmaker(bind=engine), lambda s: s.add(new_user))
    return jsonify(user_id=user_uuid), 200

def find_user_helper(session, user_id):
    user = session.query(User).filter(User.user_id == user_id).one()
    return user

@app.get('/find_user/<user_id>')
def find_user(user_id: str):
    try:
        # expire_on_commit=False to reuse returned User object attrs
        ret_user = run_transaction(
            sessionmaker(bind=engine, expire_on_commit=False),
            lambda s: find_user_helper(s, user_id)
        )

        user_dict = ret_user.to_dict()
        user_dict.pop('id') # remove id from the user dict

        return jsonify(user_dict), 200
    except NoResultFound:
        return "No user was found", 400
    except MultipleResultsFound:
        return "Multiple users were found while one is expected", 400

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
        return jsonify(done=True), 200
    except NoResultFound:
        print("No user was found")
    except MultipleResultsFound:
        print("Multiple users were found while one is expected")
    return jsonify(done=False), 400

def pay_helper(session, user_id, order_id, amount):
    user = session.query(User).filter(User.user_id == user_id).one()
    existing_payment = session.query(Payment).filter(
        Payment.user_id == user_id,
        Payment.order_id == order_id
    ).first()

    if existing_payment:
        if not existing_payment.paid:
                if user.credit >= amount:
                    user.credit -= amount
                    existing_payment.paid = True
                else:
                    raise NotEnoughCreditException()
    else:
        if user.credit >= amount:
            user.credit -= amount
        else:
            raise NotEnoughCreditException()
        new_payment = Payment(user_id=user_id, order_id=order_id, amount=amount, paid=True)
        session.add(new_payment)

    
@app.post('/pay/<user_id>/<order_id>/<int:amount>')
def pay(user_id: str, order_id: str, amount: int):
    try:
        run_transaction(
            sessionmaker(bind=engine),
            lambda s: pay_helper(s, user_id, order_id, amount)
        )
        return '', 200
    except NoResultFound:
        return "No user or payment was found", 400
    except MultipleResultsFound:
        return "Multiple users or payments were found while one is expected", 400
    except NotEnoughCreditException as e:
        return str(e), 400

def cancel_payment_helper(session, user_id, order_id):
    user = session.query(User).filter(User.user_id == user_id).one()
    payment = session.query(Payment).filter(
        Payment.user_id == user_id,
        Payment.order_id == order_id
    ).first()
    if payment.paid:
        payment.paid = False
        user.credit += payment.amount
    
@app.post('/cancel/<user_id>/<order_id>')
def cancel_payment(user_id: str, order_id: str):
    try:
        run_transaction(
            sessionmaker(bind=engine), 
            lambda s: cancel_payment_helper(s, user_id, order_id)
        )
        return '', 200
    except NoResultFound:
        return "No user or payment was found", 400
    except MultipleResultsFound:
        return "Multiple users or payments were found while one is expected", 400


def status_helper(session, user_id, order_id):
    payment = session \
        .query(Payment) \
        .filter(
            Payment.user_id == user_id, # and
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