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
Api module using the Flask framework.
"""

import logging
import flask
from flask_restx import Resource, Api, reqparse, inputs
from OMWebService import omc_proxy, util, svg_writer, settings

log = logging.getLogger(__name__)

api = Api(version="1.0", title="OMWebService API", description="OMWebService API Documentation")

@api.errorhandler
def defaultErrorHandler(error):
  """Default error handler"""
  return {"message": str(error)}, getattr(error, "code", 500)

@api.route("/version")
class Version(Resource):
  """End point to get OpenModelica version"""
  @classmethod
  def get(cls):
    """Gets the OpenModelica version"""
    return omc_proxy.sendCommand("getVersion()")

@api.route("/library-nodes/")
class LibraryNodes(Resource):
  """End point to get library nodes as json"""
  parser = reqparse.RequestParser()
  parser.add_argument("name", default = "AllLoadedClasses", help = "A Modelica node name")
  parser.add_argument("recursive", type = inputs.boolean, default = True, help = "List all node names recursively")
  parser.add_argument("sort", type = inputs.boolean, default = False, help = "Sort the node names")

  @api.expect(parser)
  def get(self):
    """Returns the list of library nodes."""
    args = self.parser.parse_args()
    nodeName = args["name"]
    recursive = args["recursive"]
    sort = util.pythonBoolToModelicaBool(args["sort"])

    nodesJson = []
    if nodeName == "AllLoadedClasses":
      classNames = omc_proxy.sendCommand("getClassNames({0}, false, false, {1}, false, true, false)".format(nodeName, sort))
      for className in classNames:
        nodesJson.append(self.getNodeJson(className, recursive, False, sort))
    else:
      nodesJson = self.getNodeJson(nodeName, recursive, True, sort)
    return nodesJson

  def getNodeJson(self, nodeName, recursive, topLevel, sort):
    """Helper method to get the list of library nodes json."""
    nodeJson = dict()
    nodeJson["id"] = nodeName
    nodeJson["displayLabel"] = util.getLastWordAfterDot(nodeName)
    classInfo = omc_proxy.sendCommand("getClassInformation({0})".format(nodeName))
    if classInfo[0] == "package":
      nodeJson["nodeType"] = "collection"
    else:
      nodeJson["nodeType"] = "component"

    (iconGraphics, connectors, parameters) = omc_proxy.getIconGraphicsConnectorsAndParameters(nodeName)

    fileName = "{0}.svg".format(util.nodeToFileName(nodeName))
    (width, height) = svg_writer.writeSVG(fileName, iconGraphics)
    fileName = "http://{0}:{1}/api/download/?filePath={2}".format(settings.FLASK_SERVER_NAME, settings.FLASK_SERVER_PORT, fileName)
    nodeJson["svg"] = util.svgJson(fileName, width, height)

    children = []
    if recursive or topLevel:
      classNames = omc_proxy.sendCommand("getClassNames({0}, false, false, {1}, false, true, false)".format(nodeName, sort))
      for className in classNames:
        children.append(self.getNodeJson("{0}.{1}".format(nodeName, className), recursive, False, sort))

    nodeJson["children"] = children

    nodeJson["connectors"] = connectors
    nodeJson["parameters"] = parameters

    return nodeJson

@api.route("/download/")
class Download(Resource):
  """End point to download the svg file."""
  parser = reqparse.RequestParser()
  parser.add_argument("filePath", required = True, default = "", help = "Path to download SVG file")

  @api.expect(parser)
  @api.produces(["image/svg+xml"])
  def get(self):
    """Downloads the contents of SVG file."""
    args = self.parser.parse_args()
    filePath = args["filePath"]
    return flask.send_file(filePath)
