from flask import Blueprint, render_template, request, flash, redirect, url_for
from flask_login import login_user, login_required, logout_user, current_user
from .models import User
from . import db

authentication = Blueprint('authentication', __name__)



@authentication.route('/signup', methods=['GET', 'POST'])
def signup():
    print("route hit", flush=True)
    if request.method == 'POST':
        print("in post method", flush=True)
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        print(username, email, password, flush=True)

        old_user = User.query.filter_by(username=username).first()
        old_email = User.query.filter_by(email=email).first()
        if old_user:
            flash("Username already exists", 'error')
        elif old_email:
            flash('Email is already in use', 'error')
        elif password != confirm_password:
            flash('Passwords don\'t match!', 'error')
        elif len(username)<3:
            flash('Username has to be a minimum of 3 characters', 'error')
        elif len(username)>30:
            flash('Username should not exceed 30 characters', 'error')
        elif len(password)<6:
            flash('Password should have a minimum of 6 characters', 'error')
        elif len(password)>30:
            flash('Password cannot exceed 30 characters', 'error')
        else:
            user = User(username=username, email=email, password=password)
            db.session.add(user)
            db.session.commit()
            print("created user", flush=True)
            flash('Account created successfully!', 'success')
            login_user(user, remember=True)
            return redirect(url_for('views.index'))


    return render_template('signup.html', user=current_user)


@authentication.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        print(username, password)

        user = User.query.filter_by(username=username).first()
        if user:
            print('found user')
            if user.password == password:
                flash('Logged in successfully!', category='success')
                login_user(user, remember=True)
                return redirect(url_for('views.index'))
            else:
                flash('Incorrect password!', category='error')
        else:
            print('no such user')
            flash('There is no account with that username', category='error')


    return render_template("login.html", user=current_user)


@authentication.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Logged out successfully!', category='success')
    return redirect(url_for('views.index'))