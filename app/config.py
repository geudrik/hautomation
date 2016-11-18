#! /usr/bin/env python2.7
# -*- coding: latin-1 -*-

import ConfigParser
import datetime
import sys
import os

parser = ConfigParser.ConfigParser()
conf_path = os.path.expanduser(os.environ.get("HOMESTACK_CONFIG", "/opt/.config/homestack"))
ret = parser.read(conf_path)

# Remember that we don't need to do anything fancy for DB connection info here
#   as the DB lib handles all of that. Part of the point of divorcing the models
#   from flask ;)

REDIS_HOST = parser.get("redis", 'host')
REDIS_PORT = parser.get("redis", 'port')

ROOT_FOLDER = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))
STATIC_FOLDER = os.path.join(ROOT_FOLDER, "app", "static")
TEMPLATE_FOLDER = os.path.join(ROOT_FOLDER, "app", "templates")

LOG_NAME = "homestack_logger"
LOG_LEVEL = parser.get("logging", 'level')

# Load crypto rounds and memory footprint
ARGON2_ROUNDS = int(parser.get("argon2", 'rounds'))
ARGON2_MEMORY = int(parser.get("argon2", 'memory'))

SECRET_KEY = parser.get("homestack", 'secret')
