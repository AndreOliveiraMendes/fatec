from main import app
from flask import flash, render_template

@app.errorhandler(404)
def page_not_found(e):
    flash(e, "danger")
    return render_template('404.html'), 404

@app.route('/under_dev')
def under_dev_page():
    return render_template('under_dev.html')