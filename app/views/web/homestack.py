#! /usr/bin/env python2.7
# -*- coding: latin-1 -*-

from flask import Blueprint
from flask import current_app
from flask import render_template

from flask_login import login_required

homestack = Blueprint("homestack", __name__, url_prefix="/homestack")


@homestack.route("/", methods=["GET"])
@login_required
def home():
    return render_template("homestack/home.html")
