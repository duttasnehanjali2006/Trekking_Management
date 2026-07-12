from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_user, logout_user, login_required, current_user
from extensions import db
from models import User

auth_bp = Blueprint('auth', __name__)


@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        password = request.form.get('password')
        contact_details = request.form.get('contact_details')
        role = request.form.get('role')

        if role not in ('staff', 'trekker'):
            flash('Invalid role selected.', 'danger')
            return redirect(url_for('auth.register'))

        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            flash('An account with this email already exists.', 'danger')
            return redirect(url_for('auth.register'))

        new_user = User(
            name=name,
            email=email,
            contact_details=contact_details,
            role=role,
            approval_status='Pending' if role == 'staff' else 'Approved',
        )
        new_user.set_password(password)

        db.session.add(new_user)
        db.session.commit()

        if role == 'staff':
            flash('Registration successful. Please wait for admin approval before logging in.', 'info')
        else:
            flash('Registration successful. You can now log in.', 'success')

        return redirect(url_for('auth.login'))

    return render_template('auth/register.html')


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')

        user = User.query.filter_by(email=email).first()

        if user is None or not user.check_password(password):
            flash('Invalid email or password.', 'danger')
            return redirect(url_for('auth.login'))

        if user.is_blacklisted:
            flash('This account has been blacklisted. Contact admin.', 'danger')
            return redirect(url_for('auth.login'))

        if user.role == 'staff' and user.approval_status != 'Approved':
            flash('Your staff account is still pending admin approval.', 'warning')
            return redirect(url_for('auth.login'))

        login_user(user)

        if user.role == 'admin':
            return redirect(url_for('admin.dashboard'))
        elif user.role == 'staff':
            return redirect(url_for('staff.dashboard'))
        else:
            return redirect(url_for('trekker.dashboard'))

    return render_template('auth/login.html')


@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('auth.login'))