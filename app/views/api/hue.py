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

    on = request.args.get('on', None)

    if on is None:
        current_app.logger.warn("No action specified for all lighting")
        return jsonify({"message":"No action specified for all lights"}), 400

    current_app.logger.info("Action: {}".format(on))

    bridges = HueBridge.filter_by(user_id=current_user.user_id)

    if on.lower() == 'true':
        for bridge in bridges:

            b = phue.Bridge(ip=bridge.address, username=bridge.user)
            lights = AllLights(b)

            lights.on = True

        current_app.logger.info("All lights turned ON")


    else:
        for bridge in bridges:

            b = phue.Bridge(ip=bridge.address, username=bridge.user)
            lights = AllLights(b)

            lights.on = False

        current_app.logger.info("All lights turned OFF")

    return jsonify({'message':'All lights have been toggled'}), 200

