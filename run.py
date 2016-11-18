#! /usr/bin/env python2.7
# -*- coding: latin-1 -*-

"""
This is the wsgi file that uwsgi/apache loads
Not a lot happening in here. Basically we just set up
the envinronment
"""

import os
import sys
import logging

# Set up an environment var for the location of our config
os.environ['HOMESTACK_CONFIG'] = "/opt/.config/homestack"

# Set up basic logging
logging.basicConfig(stream=sys.stderr, level=logging.ERROR)

# Ensure we've got import access (local shit)
sys.path.insert(0, os.path.dirname(os.path.realpath(__file__)))
sys.path.append("/opt/homestack")

# Actually import our application now
from app import create_app
application = create_app()

#allow werkzeug to work with uWSGI
if (application.debug):
    from werkzeug.debug import DebuggedApplication
    application.wsgi_app = DebuggedApplication(application.wsgi_app, True)

if __name__ == "__main__":
    application.run(host='0.0.0.0', debug=True)
