#! /usr/bin/env python2.7
# -*- coding: latin-1 -*-

from flask import _app_ctx_stack

from hsdb import User
from hsdb import Password
from hsdb import UserGroup
from hsdb import Role
from hsdb import ApiKey
from hsdb import HueBridge

from hsdb import HomestackDatabase

from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm import scoped_session

# This stores the session within the context of our flask app
HomestackDatabase._session = scoped_session(
    sessionmaker(),
    scopefunc=_app_ctx_stack.__ident_func__)
