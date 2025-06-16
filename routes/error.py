from main import app
from flask import render_template

@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

@app.route('/under_dev')
def under_dev_page():
    return render_template('under_dev.html')