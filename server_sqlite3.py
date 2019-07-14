from flask import Flask, render_template, request, redirect, session, flash, get_flashed_messages
from flask_bcrypt import Bcrypt
from sqlite3connection import connectToSQLite3
from datetime import datetime
import re
import os
import my_utils
app = Flask(__name__)

app.secret_key = 'darksecret'

dbname = os.environ['HOME']+'/dbname.db'

@app.route("/")
def mainpage():
    print(get_flashed_messages())
    session.clear()
    return render_template("index.html")

if __name__ == "__main__":
    app.run(debug=True)