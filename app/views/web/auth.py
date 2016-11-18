#! /usr/bin/env python2.7
# -*- coding: latin-1 -*-

from flask import Blueprint
from flask import current_app
from flask import render_template
from flask import redirect
from flask import request
from flask import url_for
from flask import jsonify
from flask import session
from flask import abort
from flask import flash

from flask_login import login_required
from flask_login import logout_user
from flask_login import login_user
from flask_login import current_user

from flask_principal import Identity
from flask_principal import AnonymousIdentity
from flask_principal import identity_changed

from app.database import User
from app.database import Password

from app.auth import admin_permission

from argon2 import argon2_hash
from datetime import datetime

import os

auth = Blueprint("auth", __name__, url_prefix="/auth")

@auth.route("/logout", methods=["GET"])
@login_required
def logout():

    # Log the user out
    logout_user()

    # Remove Flask-Principal set session keys (for good measure)
    for k in ('identity.name', 'identity.auth_time'):
        session.pop(key, None)

    # Change the current user in Flask-Principal to an anonymous user
    identity_changed.send(current_app._get_current_object(), identity=AnonymousIdentity())

    return redirect(url_for('auth.login'))

@auth.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "GET":
        return render_template("login.html")

    username = request.form.get('username', None)
    password = request.form.get('password', None)

    if not username or not password:
        flash("You're bad at this game. Enter a username and password to log in")
        return render_template("login.html"), 400

    # Ensure that we're working with utf8 strings as hashlib doesn't accept unicode
    try:
        username = username.encode('utf-8')
        password = password.encode('utf-8')
    except TypeError:
        flash("You're bad at this game. The username and/or password you entered isn't within the UTF-8 character set. Try again...")
        return render_template("login.html"), 400

    # Attempt to get a user object
    current_app.logger.debug("Attempting to instantiate User object for {}".format(username))
    user = User.filter_by(username=username).first()
    if not user:
        flash("Invalid username/password")
        return render_template("login.html"), 400

    # Set our hashing args
    rounds = current_app.config['ARGON2_ROUNDS']
    memory = current_app.config['ARGON2_MEMORY']

    # If we're asking for our admin user, AND last login==create timestamp (eg: first login)
    #   use default shizzle
    if username == "admin" and user.time == user.timestamp:
        current_app.logger.warn("Admin first-login detetected. Forcing default argon2 time complexity requirements")
        rounds = 2000
        memory = 1024

    current_app.logger.info("Attempting to pull password row for {}".format(user.username))
    pw = Password.filter_by(hashed_password=bytearray(argon2_hash(password, user.password_salt, t=rounds, m=memory))).first()
    if not pw:
        flash("Invalid username/password")
        return render_template("login.html"), 400

    # If this is an admin first-login, force pass change
    if username == "admin" and pw and user and user.time == user.timestamp:
        current_app.logger.warn("Admin first-login detetected. Logging admin in, and redirecting to change password")
        login_user(user, remember=True)
        identity_changed.send(current_app._get_current_object(), identity=Identity(user.user_id))
        return redirect(url_for('auth.admin_first_login'))

    # Looks like we have a valid user, update last-login
    user.timestamp = datetime.utcnow()
    user._session.commit()
    user._session.flush()

    # Log this user in
    login_user(user, remember=True)

    # Tell Flask-Principal that our identity changed
    identity_changed.send(current_app._get_current_object(), identity=Identity(user.user_id))

    # Send the user on their way
    return redirect(url_for("homestack.home"))

@auth.route("/admin-first-login", methods=["GET", "POST"])
@admin_permission.require()
def admin_first_login():

    # We've been redirected to a first login, so show our form if first-login
    if request.method == "GET":

        # This endpoint is not usable by anyone other than admin user, on first login
        if current_user.timestamp != current_user.time or current_user.username != 'admin':
            return redirect(url_for('homestack.home'))

        return render_template("admin_first_login.html")


    # We're posting, but before we do anythig check again to make sure this is a valid request
    #   We can only run this if we're the admin user and the timestamps are equal (indicated never logged in)
    if current_user.timestamp != current_user.time or current_user.username != 'admin':
        return redirect(url_for('homestack.home'))

    password1 = request.form.get('password', None)
    password2 = request.form.get('password_confirm', None)
    if not password1 or not password2 or password1 != password2:
        flash("Passwords did not match. Try harder.")
        return render_template("login.html"), 400

    # Ensure that we're working with utf8 strings as hashlib doesn't accept unicode
    try:
        password1 = password1.encode('utf-8')
        password2 = password2.encode('utf-8')
    except TypeError:
        flash("The submitted passwords don't fall within the UTF-8 character set. Try again...")
        return render_template("login.html"), 400

    # Looks like this is in fact a prelim admin password change. Change it, update
    #   timestamp, and log the user out (force a re-auth). Note that this _ALSO_
    #   changes the users salt (done every time the password is changed)

    # Update user info
    current_user.timestamp = datetime.utcnow()
    current_user.password_salt = os.urandom(32)
    current_user._session.commit()
    current_user._session.flush()

    # Set new password
    rounds = current_app.config['ARGON2_ROUNDS']
    memory = current_app.config['ARGON2_MEMORY']
    Password.insert(hashed_password=bytearray(argon2_hash(password1, current_user.password_salt, t=rounds, m=memory)))
    current_user._session.commit()

    # Forcefully log the user out and send them back to logout (double-check)
    # Log the user out
    logout_user()

    # Remove Flask-Principal set session keys (for good measure)
    for key in ('identity.name', 'identity.auth_time'):
        session.pop(key, None)

    # Change the current user in Flask-Principal to an anonymous user
    identity_changed.send(current_app._get_current_object(), identity=AnonymousIdentity())

    # This should redirect a second time straight to login
    return redirect(url_for('auth.logout'))
