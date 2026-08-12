from flask import Blueprint, flash, redirect, render_template, request, session, url_for

from app.decorators.decorators import admin_required
from app.extensions import db
from app.models.usuarios import Usuarios
from .handler import send_test_email_apppassword


bp = Blueprint('debug', __name__, url_prefix='/debug')

@admin_required
@bp.route('/')
def debug_menu():
    userid = session.get('userid')
    user = db.get_or_404(Usuarios, userid)

    return render_template('debug/debug_menu.html', user=user)

@bp.route('/mail-test', methods=['GET', 'POST'])
def mail_test_route():
    userid = session.get('userid')
    user = db.get_or_404(Usuarios, userid)

    if request.method == 'POST':
        email = request.form['email']

        success, message = send_test_email_apppassword(email)
        flash(message, 'success' if success else 'danger')
        
        return redirect(url_for('debug.mail_test_route'))

    return render_template('debug/mail_test.html', user=user)