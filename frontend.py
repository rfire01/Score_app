import re
import random
import string

from flask import Flask, render_template, request, url_for, flash, redirect
import dictdatabase as DDB

from config import REQUIRED_POINTS, Bids
from utils import update_users, send_password

app = Flask(__name__)


def add_access(email):
    if DDB.at('accesses', key=email).exists():
        new_accesses = DDB.at('accesses', key=email).read() + 1
    else:
        new_accesses = 1

    with DDB.at("accesses").session() as (session, accesses):
        accesses[email] = new_accesses

        session.write()

def validate_user(email, password):
    if not DDB.at('accounts').exists():
        DDB.at('accounts').create({})

    #print(DDB.at('accounts', key=email).exists())
    #print(DDB.at('accounts', key=email).read, password)
    if DDB.at('accounts', key=email).exists():
        if DDB.at('accounts', key=email).read() == password:
            return True

        return "Incorrect password. In case you forogt the password, click on 'send_password' in order to get it to your email (make sure to check spam if it is not in inbox)."

    #update_users()
    if DDB.at('users', key=email).exists():
        with DDB.at("accounts").session() as (session, accounts):
            new_pass = ''.join(random.choices(string.ascii_uppercase, k=2) + random.choices(string.digits, k=2))
            accounts[email] = new_pass
            session.write()

        return "Incorrect password. In case you forogt the password, click on 'send_password' in order to get it to your email (make sure to check spam if it is not in inbox)."

    return "Email does not exists, make sure it is written correctly."
    

def generate_password(email):
    if DDB.at('accounts', key=email).exists():
        return DDB.at('accounts', key=email).read()

    if DDB.at('users', key=email).exists():
        with DDB.at("accounts").session() as (session, accounts):
            new_pass = ''.join(random.choices(string.ascii_uppercase, k=2) + random.choices(string.digits, k=2))
            accounts[email] = new_pass
            session.write()
        return new_pass

    return False


@app.route("/", methods=["GET", "POST"])
def home():
    score = 0
    email = ''
    password = ''
    error_msg = ''
    show_output = False
    valid_user = False
    data = {}
    if request.method == "POST":
        email = re.sub('[^A-Za-z0-9@.]+', '', request.form["email"])
        if 'send' in request.form:
            password = generate_password(email)
            if password:
                send_password(email, password)
                error_msg = f'Password was sent to {email}'
            else:
                error_msg = 'Email does not exists, make sure it is written correctly.'
            password = request.form['password']

        else:
            password = request.form['password'].upper()
            # print(email, DDB.at('scores', key=email).exists())
            validation = validate_user(email, password)
    
            if validation == True:
                add_access(email)
                scores = DDB.at('scores', key=email).read()
                valid_user = True

                data = {'In a Pinch': scores[Bids.PINCH.value],
                        'Willing': scores[Bids.WILLING.value],'Eager': scores[Bids.EAGER.value]}
                score = sum(data.values())
            else:
                error_msg = validation

        show_output = True

    params = {'score':score, 'requirement':REQUIRED_POINTS, 'email':email, 'password': password,
              'show_output': show_output, 'valid_user': valid_user, 'error_msg': error_msg,
              'data': data}
    return render_template("home.html", **params)


if __name__ == "__main__":
    app.run(ssl_context='adhoc')
