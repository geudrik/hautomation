#! /usr/bin/env python2.7
# -*- coding: latin-1 -*-

from flask import Blueprint
from flask import current_app
from flask import jsonify
from flask import request

from flask_login import current_user
from flask_login import login_required

from app.database import HueBridge

from phue import Bridge
from phue import AllLights

hue = Blueprint("hue", __name__, url_prefix="/api/v1/hue")

@hue.route("/toggle/lights", methods=["PUT"])
@login_required
def all_lights():
    """
    Toggle ALL lights, for all bridges, for this user
    """

    on = request.form.get('on', None)
    if on is None:
        return jsonify({"message":"No action specified for all lights"}), 400

    bridges = HueBridge.filter_by(user_id=current_user.user_id)
    for bridge in bridges:

        b = Bridge(ip=bridge.address, username=bridge.user)
        lights = AllLights(b)
        lights.on = True if on.lower() == 'true' else False

    return jsonify({'message':'All lights have been toggled'}), 200

@hue.route("/toggle/group/<groupname>", methods=["PUT"])
@login_required
def group_lights(groupname):

    # Not sure why, but the google assistant/Maker on IFTTT doubles up on `the`
    groupname = groupname.lower().replace('the ', '')

    on = request.form.get('on', None)
    if on is None:
        return jsonify({"message":"No action specified for all lights in {}".format(groupname)}), 400

    bridges = HueBridge.filter_by(user_id=current_user.user_id)
    for bridge in bridges:

        b = Bridge(ip=bridge.address, username=bridge.user)
        lights = b.get_light_objects()
        group = b.get_group(groupname.title())
        if not group:
            continue

        for light_id in group['lights']:
            current_app.logger.debug("`on` : {} | light_id : {}".format(on, light_id))
            lights[light_id].on = True if on.lower() == 'true' else False

    return jsonify({'message':'All lights have been toggled'}), 200



