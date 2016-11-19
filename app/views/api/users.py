#! /usr/bin/env python2.7
# -*- coding: latin-1 -*-

from flask import Blueprint
from flask import current_app
from flask import jsonify
from flask import request

from flask_login import current_user
from flask_login import login_required

from app.database import ApiKey

users = Blueprint("users", __name__, url_prefix="/api/v1/users")

@users.route("/apikeys", methods=["GET"])
@users.route("/apikeys/", methods=["GET"])
@login_required
def apikey_list():

    keys = ApiKey.filter_by(user_id=current_user.user_id).all()
    if keys:
        return jsonify({"items":[key.serialize() for key in keys]}), 200

    return jsonify({"error":"No API keys found for your user. Perhaps you should create one?"}), 404

@users.route("/apikey", methods=["POST", "PUT", "DELETE"], defaults={'key_id':None})
@users.route("/apikey/<int:key_id>", methods=["POST", "PUT", "DELETE"])
@login_required
def apikey_manage(key_id):

    # We're creating a new key
    if request.method == "POST":

        desc = request.form.get("description", None)
        if not desc:
            return jsonify({"error":"No `description` form param specified"}), 400

        try:
            key = ApiKey.insert(user_id=current_user.user_id, description=desc)
            return jsonify(key.serialize()), 200
        except Exception as e:
            current_app.logger.exception(e)

        return jsonify({"error":"A server error was encountered while attempting to create the new api key"}), 500

    # We're updating the description for this key
    elif request.method == "PUT":

        desc = request.form.get("description", None)

        if not desc:
            return jsonify({"error":"No `description` form param specified"}), 400

        if not key_id:
            return jsonify({"error":"No `key_id` url param specified"}), 400


        key = ApiKey.filter_by(key_id=key_id, user_id=current_user.user_id).first()
        if not key:
            return jsonify({"error":"An API Key with that ID does not exist for your user"}), 400

        try:
            key.description = desc
            key._session.commit()
            key._session.flush()
            return jsonify(key.serialize()), 200

        except Exception as e:
            current_app.logger.exception(e)

        return jsonify({'error':'An error was encountered attempting to remove the key'}), 500

    # We're deleting a key
    elif request.method == "DELETE":

        if not key_id:
            return jsonify({"error":"No `key_id` url param specified"}), 400

        try:

            key = ApiKey.filter_by(user_id=current_user.user_id, key_id=key_id).first()
            if not key:
                return jsonify({"error":"An API Key with that ID does not exist for your user"}), 400

            key.delete()
            return jsonify({'message':'Key deleted successfully'}), 200

        except Exception as e:
            current_app.logger.exception(e)

        return jsonify({'error':'An error was encountered attempting to remove the key'}), 500

