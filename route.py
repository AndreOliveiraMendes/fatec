from main import app
from flask import render_template, redirect, url_for

@app.route("/")
def home():
    return render_template("homepage.html")