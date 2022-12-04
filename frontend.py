from flask import Flask, render_template, request, url_for, flash, redirect
import dictdatabase as DDB

app = Flask(__name__)


@app.route("/", methods=["GET", "POST"])
def home():
    score = 0
    if request.method == "POST":
        if DDB.at('scores', key=request.form["email"]).exists():
            score = DDB.at('scores', key=request.form["email"]).read()

    return render_template("home.html", score=score, requirement=200)


if __name__ == "__main__":
    app.run()