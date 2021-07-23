from main import app
from flask import render_template, session


@app.route("/")
def index():
    if session.get("user_id") is not None:
        pass
    else:
        return render_template("index.html")
