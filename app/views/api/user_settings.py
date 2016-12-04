#! /usr/bin/env python2.7
# -*- coding: latin-1 -*-

from flask import Blueprint
from flask import current_app
from flask import jsonify
from flask import request

from flask_login import current_user
from flask_login import login_required

from app.database import HueBridge

user_settings = Blueprint("user_settings", __name__, url_prefix="/api/v1/user/settings")

@user_settings.route("/hue/bridge", methods=["GET", "POST"])
@login_required
def huebridges_list():
    """
    Return a list of all configured Hue Bridges for this user
    """
    if request.method == "GET":
        ret = {}
        bridges = HueBridge.filter_by(user_id=current_user.user_id)
        for bridge in bridges:
            ret[bridge.name] = bridge.serialize()

        return jsonify(ret), 200

    # Create new Hue Bridge
    elif request.method == "POST":
        bridge_name = request.form.get("bridge_name", None)
        bridge_address = request.form.get("bridge_address", None)
        bridge_user = request.form.get("bridge_user", None)

        if not bridge_name:
            return jsonify({"error":"No `bridge_name` form param specified"}), 400

        if not bridge_address:
            return jsonify({"error":"No `bridge_address` form param specified"}), 400

        if not bridge_user:
            return jsonify({"error":"No `bridge_user` form param specified"}), 400

        try:
            bridge = HueBridge.insert(user_id=current_user.user_id, name=bridge_name, address=bridge_address, user=bridge_user)
            return jsonify(bridge.serialize()), 200
        except Exception as e:
            current_app.logger.exception(e)

        return jsonify({"error":"A server error was encountered while attempting to add a Hue Bridge."}), 500

@user_settings.route("/hue/bridge/<int:bridge_id>", methods=["PUT", "DELETE"])
@login_required
def huebridges_modify(bridge_id):

    # Delete a huge bridge
    if request.method == "DELETE":

        bridge = HueBridge.filter_by(user_id=current_user.user_id, bridge_id=bridge_id).first()
        if bridge:
            bridge.delete()

        else:
            current_app.logger.error("DELETE attempt failed for Hue Bridge", extra={'bridge_id':bridge_id, 'user_id':current_user.user_id})
            return jsonify({'error':'This bridge could not be found for this user'}), 400

        return jsonify({'message':'Bridge deleted successfully'}), 200

    # Udpate a hue bridge
    elif request.method == "PUT":

        bridge_name = request.form.get("bridge_name", None)
        bridge_address = request.form.get("bridge_address", None)
        bridge_user = request.form.get("bridge_user", None)

        if not bridge_name:
            return jsonify({"error":"No `bridge_name` form param specified"}), 400

        if not bridge_address:
            return jsonify({"error":"No `bridge_address` form param specified"}), 400

        if not bridge_user:
            return jsonify({"error":"No `bridge_user` form param specified"}), 400

        try:
            bridge = HueBridge.filter_by(bridge_id=bridge_id, user_id=current_user.user_id)
            bridge.name = bridge_name
            bridge.address = bridge_address
            bridge.user = bridge_user
            bridge._session.commit()
            bridge._session.flush()
            return jsonify(bridge.serialize()), 200
        except Exception as e:
            current_app.logger.exception(e)

        return jsonify({"error":"A server error was encountered while attempting to update your Hue Bridge."}), 500


