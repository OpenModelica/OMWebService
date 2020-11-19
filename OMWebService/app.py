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

import logging
from flask import Flask, Blueprint
from OMWebService import api, settings

log = logging.getLogger(__name__)

app = Flask(__name__)

def configureApp():
  """Configure the app."""
  logging.basicConfig(level=logging.DEBUG)

def initializeApp():
  """Initialize the app."""
  configureApp()

  blueprint = Blueprint("api", __name__, url_prefix="/api")
  api.api.init_app(blueprint)
  app.register_blueprint(blueprint)

def main():
  """web app main entry point."""
  initializeApp()
  app.run(host=settings.FLASK_SERVER_NAME, port=settings.FLASK_SERVER_PORT, debug=settings.FLASK_DEBUG)

if __name__ == "__main__":
  main()
