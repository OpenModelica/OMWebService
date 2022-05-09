#!/usr/bin/env python
# -*- coding: utf-8 -*-

# This file is part of OpenModelica.
# Copyright (c) 1998-CurrentYear, Open Source Modelica Consortium (OSMC),
# c/o Linköpings universitet, Department of Computer and Information Science,
# SE-58183 Linköping, Sweden.

# All rights reserved.

# THIS PROGRAM IS PROVIDED UNDER THE TERMS OF GPL VERSION 3 LICENSE OR
# THIS OSMC PUBLIC LICENSE (OSMC-PL) VERSION 1.2.
# ANY USE, REPRODUCTION OR DISTRIBUTION OF THIS PROGRAM CONSTITUTES
# RECIPIENT'S ACCEPTANCE OF THE OSMC PUBLIC LICENSE OR THE GPL VERSION 3,
# ACCORDING TO RECIPIENTS CHOICE.

# The OpenModelica software and the Open Source Modelica
# Consortium (OSMC) Public License (OSMC-PL) are obtained
# from OSMC, either from the above address,
# from the URLs: http://www.ida.liu.se/projects/OpenModelica or
# http://www.openmodelica.org, and in the OpenModelica distribution.
# GNU version 3 is obtained from: http://www.gnu.org/copyleft/gpl.html.

# This program is distributed WITHOUT ANY WARRANTY; without
# even the implied warranty of  MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE, EXCEPT AS EXPRESSLY SET FORTH
# IN THE BY RECIPIENT SELECTED SUBSIDIARY LICENSE CONDITIONS OF OSMC-PL.

# See the full OSMC Public License conditions for more details.

"""
Web service application
"""

import os
import logging
from flask import Flask, Blueprint
from Service import api

log = logging.getLogger(__name__)

def createApp():
  """Create the Flask app."""
  app = Flask(__name__)
  blueprint = Blueprint("api", __name__, url_prefix="/api")
  api.api.init_app(blueprint)
  app.register_blueprint(blueprint)

  if os.environ.get("FLASK_ENV") == "development":
    app.config.from_object('config.DevelopmentConfig')
    logging.basicConfig(level=logging.DEBUG)
  else:
    app.config.from_object('config.ProductionConfig')
    logging.basicConfig(level=logging.WARNING)

  if not os.path.exists(app.config['TMPDIR']):
    os.makedirs(app.config['TMPDIR'])

  return app

def main():
  """web app main entry point."""
  app = createApp()
  dockerApp = os.environ.get('DOCKER_APP', False)
  if dockerApp:
    app.run(host="0.0.0.0", port="8080") # This tells your operating system to listen on all public IPs.
  else:
    app.run()

if __name__ == "__main__":
  main()