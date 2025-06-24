from main import app
from flask import session, render_template
from auxiliar.auxiliar_routes import get_user_info

@app.route("/")
def home():
    userid = session.get('userid')
    username, perm = get_user_info(userid)
    return render_template("homepage.html", username=username, perm=perm)