import re

from flask import Flask, render_template, request, url_for, flash, redirect
import dictdatabase as DDB

from config import REQUIRED_POINTS, Bids

app = Flask(__name__)


@app.route("/", methods=["GET", "POST"])
def home():
    score = 0
    email = ''
    show_output = False
    valid_user = False
    data = {}
    if request.method == "POST":
        email = re.sub('[^A-Za-z0-9@.]+', '', request.form["email"])
        # print(email, DDB.at('scores', key=email).exists())
        if DDB.at('scores', key=email).exists():
            scores = DDB.at('scores', key=email).read()
            valid_user = True

            data = {'In a Pinch': scores[Bids.PINCH.value],
                    'Willing': scores[Bids.WILLING.value],'Eager': scores[Bids.EAGER.value]}
            score = sum(data.values())

        show_output = True

    params = {'score':score, 'requirement':REQUIRED_POINTS, 'email':email,
              'show_output': show_output, 'valid_user': valid_user,
              'data': data}
    return render_template("home.html", **params)


if __name__ == "__main__":
    app.run(ssl_context='adhoc')