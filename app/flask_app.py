#! /usr/bin/env python2.7
# -*- coding: latin-1 -*-

from flask import g
from flask import Flask
from flask import url_for
from flask import request
from flask import session
from flask import jsonify
from flask import redirect
from flask import current_app
from flask import render_template

from flask_login import LoginManager
from flask_login import login_user
from flask_login import current_user

from flask_principal import UserNeed
from flask_principal import RoleNeed
from flask_principal import Principal
from flask_principal import Identity
from flask_principal import identity_loaded
from flask_principal import identity_changed

from auth import map_api_key_to_user
from auth import admin_permission

import os
import sys
import time
import json
import redis
import logging
import traceback

from config import STATIC_FOLDER


def create_app(config=None, *args):
    """
    Create our flask application
    args:
        config: the flask config object
        *args: Includes an instance of `mod_wsgi.Adapter`
    """

    application = Flask("homestack_flask_instance", static_folder=STATIC_FOLDER)
    configure_app(application)
    configure_logging(application)
    configure_hooks(application)
    configure_extensions(application)
    configure_blueprints(application)
    configure_handlers(application)

    return application


def configure_app(application):
    """
    Configure our application
    args:
        application: the flask app
    """

    # http://flask.pocoo.org/docs/api/#configuration
    application.config.from_object("app.config")
    application.static_folder = application.config['STATIC_FOLDER']
    application.template_folder = application.config['TEMPLATE_FOLDER']


def configure_extensions(application):
    """
    Configure Flask and other extensions used by the app
    args:
        application: the flask app
    """

    from database import User

    # FOrce redirect to login page if unauthenticated and requesting authd page
    login_manager = LoginManager()
    login_manager.login_view = '/auth/login'
    login_manager.init_app(application)

    # Load user
    @login_manager.user_loader
    def load_user(user_id):
        user = User.filter_by(user_id=user_id).first()
        return user

    # Set up flask-principal
    principal = Principal(application)

    # Set up identitiy loader. This loads roles for a newly logged in user
    # https://pythonhosted.org/Flask-Principal/#user-information-providers
    @identity_loaded.connect_via(application)
    def on_ident_loaded(sender, identity):

        identity.user = current_user

        # Add UserNeed to our identity
        if hasattr(current_user, 'user_id'):
            identity.provides.add(UserNeed(current_user.user_id))

        # Our User model provides for roles. This updates the identity with roles
        #   for this user
        if hasattr(current_user, 'user_groups'):
            for group in current_user.user_groups:
                for role in group.roles:
                    identity.provides.add(RoleNeed(role.name))
            identity.provides.add(RoleNeed("authenticated"))

    # This is basically a hack to combat the session-reload issue when a session is forgotten
    #   eg: the browser window is closed. This will destroy the session, thus our ident_loader
    #       has no session to reload, despite still  being logged in via flask-logins cookie
    #   To combat this, we add a new identity_loader which will only run when a session expires
    #
    #   Ref: https://stackoverflow.com/questions/24487449/flask-principal-flask-login-remember-me-and-identity-loaded
    @principal.identity_loader
    def load_ident_when_session_expires():
        if hasattr(current_user, 'user_id'):
            return Identity(current_user.user_id)


def configure_blueprints(application):
    """
    Configure blueprints in our views
    args:
        application: the flask app
    """
    from views.web.homestack import homestack
    from views.web.auth import auth
    from views.api.users import users
    from views.api.user_settings import user_settings
    from views.api.hue import hue

    # Make life easy on ourselves
    blueprints = [
        homestack,
        auth,
        users,
        user_settings,
        hue
    ]
    for bp in blueprints:
        application.register_blueprint(bp)

    # Our default route override
    @application.route("/", methods=['GET'])
    def index():
        return redirect(url_for('homestack.home'))

    # Hack and slash route to show a "sitemap"
    @application.route("/sitemap", methods=['GET'])
    def sitemap():
        methods = ['GET', 'POST', 'PUT', 'UPDATE', 'DELETE']
        links = []
        def has_no_empty_params(rule):
            defaults = rule.defaults if rule.defaults is not None else ()
            arguments = rule.arguments if rule.arguments is not None else ()
            return len(defaults) >= len(arguments)
        for rule in application.url_map.iter_rules():
            if any(x in methods for x in rule.methods) and has_no_empty_params(rule):
                url = url_for(rule.endpoint)
                links.append((url, rule.endpoint, list(rule.methods - set(['HEAD', 'OPTIONS']))))
        return jsonify(links), 200


def configure_logging(application):
    """
    Configure our loggers, used through the app
    args:
        application: the flask application
    """

    # Set up logging
    formatter = logging.Formatter('%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]')
    application.logger_name = application.config['LOG_NAME']
    log_level = application.config["LOG_LEVEL"]
    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(formatter)
    stream_handler.setLevel(log_level)

    try:
        root_handler = logging.getLogger().handlers[0]
        root_handler.setFormatter(formatter)

    except:
        pass

    # Add logging to our application!
    loggers = [application.logger, logging.getLogger()]
    for logger in loggers:

        # Remove default log handlers
        for handler in logger.handlers:
            logger.removeHandler(handler)

        logger.addHandler(stream_handler)


def configure_hooks(application):
    """
    Configure a bunch of hooks and additional handlers
    args:
        application: our flassk app
    """

    @application.before_request
    def authenticate_via_api_key():

        # Default to try to get our API key
        api_key = request.headers.get("X-API-Key", None)

        # IFTTT doesn't let us specify headers, so we gotta URL encode this bad-boi
        if 'application/x-www-form-urlencoded' in request.headers.get('Content-Type', []):
            api_key = request.form.get('X-API-Key', None)
            application.logger.debug("URL Encoded API Request made for {}".format(api_key))

        if api_key:

            # Attempt to get a User instance for this key
            user = map_api_key_to_user(api_key)

            if user:
                login_user(user, remember=True)
                identity_changed.send(current_app._get_current_object(), identity=Identity(user.user_id))
                application.logger.debug("Logged in user {}".format(user.username))

            return jsonify({'error':'unknown API key'}), 403

    # Set up our globals for each request
    @application.before_request
    def set_globals():

        # Boolean we track in `g` to see if we're requesting JSON be returned
        g.json = False
        if 'application/json' in request.headers.get('ACCEPT', []) or request.path.startswith("/api"):
            g.json = True

        # Add a redis connection to g
        g.redis = redis.StrictRedis(
            host=application.config['REDIS_HOST'],
            port=application.config['REDIS_PORT'],
            )


    # Clean out our DB sessions _before_ each request
    @application.before_request
    def freshen_db_sessions():

        import database
        database.HomestackDatabase._session.remove()

    # Log a bunch of additional request data for debugging purposes
    @application.before_request
    def log_debug_info():

        # Trim the fluff off of our request object
        _request = dict(request.headers.__dict__['environ'])
        for key in _request.keys():
            if key.startswith('werkzeug') or key.startswith('wsgi') or key.startswith('mod_wsgi'):
                del(_request[key])

        # Write our debug entry
        application.logger.debug("[{}] request made to {}".format(request.method, request.endpoint), extra=_request)

    # Set up an ability to log the execution time of an endpoint
    @application.before_request
    def endpoint_exec_start_time():

        if request.path.startswith('/static/') or 'favicon' in request.path:
            return

        request.start_time = time.time()

    # Clean out our DB sessions _after_ each request, too, for good measure
    @application.after_request
    def clean_db_sessions(req):

        import database
        database.HomestackDatabase._session.remove()
        return req

    @application.after_request
    def endpoint_exec_end_time(req):

        print request.path
        if request.path.startswith('/static/') or 'favicon' in request.path:
            return req

        try:
            start_time = request.start_time
            application.logger.info("Execution of {} took {} seconds".format(request.endpoint, int(time.time() - start_time)))
        except:
            pass

        return req


def configure_handlers(application):
    """
    Configure generic error handlers, for good measure.
    TODO: We need to add in UI vs. JSON responses depending on the context of the request being made
    args:
        application: our flask app
    """
    @application.errorhandler(400)
    def error_400(err):
        current_app.logger.error("400 : {0} | {1}".format(request.url, err))
        return jsonify({'message':'{0}'.format(err)}), 400

    @application.errorhandler(401)
    def error_401(err):
        current_app.logger.error("401 : {0} | {1}".format(request.url, err))
        return jsonify({'message':'{0}'.format(err)}), 401

    @application.errorhandler(403)
    def error_403(err):
        current_app.logger.error("403 : {0} | {1}".format(request.url, err))
        if g.json:
            jsonify({'message':'{0}'.format(err)}), 403
        return render_template("error/403.html"), 403

    @application.errorhandler(404)
    def error_404(err):
        current_app.logger.error("404 : {0} | {1}".format(request.url, err))
        if g.json:
            jsonify({'message':'{0}'.format(err)}), 404
        return render_template("error/404.html"), 404

    @application.errorhandler(405)
    def error_405(err):
        current_app.logger.error("405 : {0} | {1}".format(request.url, err))
        return jsonify({'message':'{0}'.format(err)}), 405

    @application.errorhandler(Exception)
    @application.errorhandler(500)
    def error_500(err):

        # Trim the fat out of our request object
        extra = dict(request.headers.__dict__['environ'])
        for key in extra.keys():
            if key.startswith('werkzeug') or key.startswith('wsgi') or key.startswith('mod_wsgi'):
                del(extra[key])

        # Log our exception
        current_app.logger.exception(err, extra=extra)

        # See if this is an admin user. If yes, dump the stacktrace
        debug = False
        if admin_permission.can():
            debug = traceback.format_exc()

        if g.json:
            return jsonify({'message':'{0}'.format(err)}), 500
        return render_template("error/500.html", debug=debug), 500
