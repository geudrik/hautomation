#! /usr/bin/env python2.7
# -*- coding: latin-1 -*-

from database import User
from database import ApiKey
from flask_principal import Permission
from flask_principal import RoleNeed

admin_permission = Permission(RoleNeed('admin'))

def map_api_key_to_user(key):
    """
    Take an input of an API key and return a User instance
    """

    key = key.strip()
    user = None

    # Attempt to get a user instance from an apikey row
    row = ApiKey.filter_by(api_key=key).first()
    if row:
        user = row.user

    return user
