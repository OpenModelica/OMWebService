#!/usr/bin/env python
# -*- coding: utf-8 -*-

__license__ = """
This file is part of OpenModelica.
Copyright (c) 1998-CurrentYear, Open Source Modelica Consortium (OSMC),
c/o Linköpings universitet, Department of Computer and Information Science,
SE-58183 Linköping, Sweden.

All rights reserved.

THIS PROGRAM IS PROVIDED UNDER THE TERMS OF GPL VERSION 3 LICENSE OR
THIS OSMC PUBLIC LICENSE (OSMC-PL) VERSION 1.2.
ANY USE, REPRODUCTION OR DISTRIBUTION OF THIS PROGRAM CONSTITUTES
RECIPIENT'S ACCEPTANCE OF THE OSMC PUBLIC LICENSE OR THE GPL VERSION 3,
ACCORDING TO RECIPIENTS CHOICE.

The OpenModelica software and the Open Source Modelica
Consortium (OSMC) Public License (OSMC-PL) are obtained
from OSMC, either from the above address,
from the URLs: http://www.ida.liu.se/projects/OpenModelica or
http://www.openmodelica.org, and in the OpenModelica distribution.
GNU version 3 is obtained from: http://www.gnu.org/copyleft/gpl.html.

This program is distributed WITHOUT ANY WARRANTY; without
even the implied warranty of  MERCHANTABILITY or FITNESS
FOR A PARTICULAR PURPOSE, EXCEPT AS EXPRESSLY SET FORTH
IN THE BY RECIPIENT SELECTED SUBSIDIARY LICENSE CONDITIONS OF OSMC-PL.

See the full OSMC Public License conditions for more details.
"""

import logging
from flask_restx import Resource, Api
import omcproxy
from flask_restx import reqparse
from flask_restx import inputs

log = logging.getLogger(__name__)

api = Api(version='1.0', title='OMWebService API', description='OMWebService API Documentation')

@api.route("/version")
class version(Resource):
  def get(self):
    return omcproxy.ask_omc("getVersion()")

@api.route("/library-nodes/")
class libraryNodes(Resource):
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
    sort = omcproxy.pythonBoolToModelicaBool(args["sort"])

    nodesJson = []
    if nodeName == "AllLoadedClasses":
      classNames = omcproxy.ask_omc("getClassNames(%s, false, false, %s, false, true, false)" % (nodeName, sort))
      for className in classNames:
        nodesJson.append(self.getNodeJson(className, recursive, False, sort))
      return nodesJson
    else:
      return self.getNodeJson(nodeName, recursive, True, sort)

  def getNodeJson(self, nodeName, recursive, topLevel, sort):
    nodeJson = dict()
    nodeJson["id"] = nodeName
    nodeJson["displayLabel"] = omcproxy.getLastWordAfterDot(nodeName)
    classInfo = omcproxy.ask_omc("getClassInformation(%s)" % (nodeName))
    if classInfo[0] == 'package':
      nodeJson["nodeType"] = "collection"
    else:
      nodeJson["nodeType"] = "component"
    nodeJson["svgPath"] = "" # add icon svg code

    children = []
    if recursive or topLevel:
      classNames = omcproxy.ask_omc("getClassNames(%s, false, false, %s, false, true, false)" % (nodeName, sort))
      for className in classNames:
        children.append(self.getNodeJson("{0}.{1}".format(nodeName, className), recursive, False, sort))

    nodeJson["children"] = children
    parameters = []
    connectors = []
    nodeJson["connectors"] = connectors
    nodeJson["parameters"] = parameters

    return nodeJson
