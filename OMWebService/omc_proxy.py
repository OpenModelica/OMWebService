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
OpenModelica kernel module. Communicates with OM compiler.
"""

import os
import logging
import base64
from OMPython import OMCSessionZMQ
from OMWebService import util, svg_writer, settings

log = logging.getLogger(__name__)
omc = OMCSessionZMQ()

def sendCommand(expression, parsed=True):
  """Sends the command to OMC."""
  log.debug("sendCommand: %s - parsed: %s", expression, parsed)

  try:
    res = omc.sendExpression(expression, parsed)
    log.debug("OMC getErrorString(): %s", omc.sendExpression("getErrorString()"))
  except Exception as ex:
    log.error("OMC failed: %s, parsed=%s with exception: %s", expression, parsed, str(ex))
    raise

  return res

# OMC setup commands

sendCommand("setCommandLineOptions(\"-d=newInst,nfAPI\")", True)

if not sendCommand("loadModel(Modelica)", True):
  log.critical("Failed to load Modelica standard library: %s", omc.sendExpression("getErrorString()"))

def getIconGraphicsConnectorsAndParametersHelper(className, iconGraphics, connectors, parameters):
  """Helper function to getIconGraphicsConnectorsAndParameters"""
  iconGraphics.append(getClassGraphics(className))
  componentsList = getComponents(className)
  if componentsList:
    componentAnnotations = getComponentAnnotations(className)

    for i, componentList in enumerate(componentsList):
      try:
        componentInfo = util.unparseStrings(componentList)
        if sendCommand("isConnector({0})".format(componentInfo[0])):
          component = dict()
          component["id"] = componentInfo[0]
          fileName = "{0}.svg".format(util.nodeToFileName(componentInfo[0]))
          (width, height) = svg_writer.writeSVG(fileName, [getClassGraphics(componentInfo[0])])
          fileName = "http://{0}:{1}/api/download/?filePath={2}".format(settings.FLASK_SERVER_NAME, settings.FLASK_SERVER_PORT, fileName)
          component["svg"] = util.svgJson(fileName, width, height)
          component["placement"] = util.componentPlacement(componentAnnotations[i])
          connectors.append(component)
        elif componentInfo[8] == "parameter":
          component = dict()
          component["id"] = componentInfo[0]
          component["displayLabel"] = componentInfo[1]
          parameters.append(component)
      except KeyError as ex:
        log.error("KeyError: %s index: %s %s", className, i+1, str(ex))
        continue

def getIconGraphicsConnectorsAndParameters(className):
  """Gets the icon annotation, connectors and parameters of a class."""
  baseClasses = []
  getBaseClasses(className, baseClasses)

  iconGraphics = []
  connectors = []
  parameters = []

  for baseClass in reversed(baseClasses):
    getIconGraphicsConnectorsAndParametersHelper(baseClass, iconGraphics, connectors, parameters)
  getIconGraphicsConnectorsAndParametersHelper(className, iconGraphics, connectors, parameters)

  return iconGraphics, connectors, parameters

def getComponents(className):
  """Gets the list of components from OMC."""
  return util.unparseArrays(sendCommand("getComponents({0}, useQuotes = true)".format(className), parsed=False))

def getComponentAnnotations(className):
  """Gets the list of components annotations from OMC."""
  componentAnnotations = sendCommand("getComponentAnnotations({0})".format(className), parsed=False)
  componentAnnotationsList = util.getStrings(util.removeFirstLastCurlBrackets(componentAnnotations))
  return componentAnnotationsList

# Note: The order of the base classes matters
def getBaseClasses(className, baseClasses):
  """Gets the list of inherited classes from OMC."""
  inheritanceCount = sendCommand("getInheritanceCount({0})".format(className))

  for i in range(1, inheritanceCount + 1):
    baseClass = sendCommand("getNthInheritedClass({0}, {1})".format(className ,str(i)))
    if baseClass not in baseClasses:
      baseClasses.append(baseClass)
      getBaseClasses(baseClass, baseClasses)

# get graphics objects from annotation Icon
def getClassGraphics(className):
  """Gets the class icon annotation from OMC."""
  iconAnnotation = sendCommand("getIconAnnotation({0})".format(className), parsed=False)

  classGraphics = dict()
  classGraphics["graphics"] = []
  classGraphics["coordinateSystem"] = {}
  classGraphics["coordinateSystem"]["extent"] = [[-100, -100], [100, 100]]
  classGraphics["coordinateSystem"]["preserveAspectRatio"] = True
  classGraphics["coordinateSystem"]["initialScale"] = 0.1
  classGraphics["coordinateSystem"]["grid"] = [2, 2]

  iconAnnotationList = util.getStrings(util.removeFirstLastCurlBrackets(iconAnnotation))
  if len(iconAnnotationList) >= 8:
    if util.isFloat(iconAnnotationList[0]) and util.isFloat(iconAnnotationList[1]) and util.isFloat(iconAnnotationList[2]) and util.isFloat(iconAnnotationList[3]):
      classGraphics["coordinateSystem"]["extent"] = [[float(iconAnnotationList[0]), float(iconAnnotationList[1])], [float(iconAnnotationList[2]), float(iconAnnotationList[3])]]
    if util.isFloat(iconAnnotationList[4]):
      classGraphics["coordinateSystem"]["preserveAspectRatio"] = bool(iconAnnotationList[4])
    if util.isFloat(iconAnnotationList[5]):
      classGraphics["coordinateSystem"]["initialScale"] = float(iconAnnotationList[5])
    if util.isFloat(iconAnnotationList[6]) and util.isFloat(iconAnnotationList[7]):
      classGraphics["coordinateSystem"]["grid"] = [float(iconAnnotationList[6]), float(iconAnnotationList[7])]

  if len(iconAnnotationList) < 9:
    return classGraphics
  shapes = util.getStrings(util.removeFirstLastCurlBrackets(iconAnnotationList[8]), "(", ")")

  for shape in shapes:
    graphicsObject = {}

    if shape.startswith("Line"):
      graphicsObject["type"] = "Line"
      shape = shape[len("Line"):]
      shapeList = util.getStrings(util.removeFirstLastParentheses(shape))
      util.parseGraphicItem(graphicsObject, shapeList)
      # 4th item of list contains the points.
      points = []
      pointsList = util.getStrings(util.removeFirstLastCurlBrackets(shapeList[3]))
      for point in pointsList:
        linePoints = util.getStrings(util.removeFirstLastCurlBrackets(point))
        points.append([float(linePoints[0]), float(linePoints[1])])
      graphicsObject["points"] = points
      # 5th item of list contains the color.
      colorList = util.getStrings(util.removeFirstLastCurlBrackets(shapeList[4]))
      graphicsObject["color"] = [int(colorList[0]), int(colorList[1]), int(colorList[2])]
      # 6th item of list contains the Line Pattern.
      graphicsObject["pattern"] = shapeList[5]
      # 7th item of list contains the Line thickness.
      graphicsObject["thickness"] = float(shapeList[6])
      # 8th item of list contains the Line Arrows.
      arrowList = util.getStrings(util.removeFirstLastCurlBrackets(shapeList[7]))
      graphicsObject["arrow"] = [arrowList[0], arrowList[1]]
      # 9th item of list contains the Line Arrow Size.
      graphicsObject["arrowSize"] = float(shapeList[8])
      # 10th item of list contains the smooth.
      graphicsObject["smooth"] = shapeList[9]
    elif shape.startswith("Rectangle"):
      graphicsObject["type"] = "Rectangle"
      shape = shape[len("Rectangle"):]
      shapeList = util.getStrings(util.removeFirstLastParentheses(shape))
      util.parseGraphicItem(graphicsObject, shapeList)
      util.parseFilledShape(graphicsObject, shapeList)
      # 9th item of list contains the border pattern.
      graphicsObject["borderPattern"] = shapeList[8]
      # 10th item is the extent points.
      extentsList = util.getStrings(util.removeFirstLastCurlBrackets(shapeList[9]))
      extentPoints1 = util.getStrings(util.removeFirstLastCurlBrackets(extentsList[0]))
      extentPoints2 = util.getStrings(util.removeFirstLastCurlBrackets(extentsList[1]))
      graphicsObject["extent"] = [[float(extentPoints1[0]), float(extentPoints1[1])], [float(extentPoints2[0]), float(extentPoints2[1])]]
      # 11th item of the list contains the corner radius.
      graphicsObject["radius"] = float(shapeList[10])
    elif shape.startswith("Polygon"):
      graphicsObject["type"] = "Polygon"
      shape = shape[len("Polygon"):]
      shapeList = util.getStrings(util.removeFirstLastParentheses(shape))
      util.parseGraphicItem(graphicsObject, shapeList)
      util.parseFilledShape(graphicsObject, shapeList)
      # 9th item of list contains the points.
      points = []
      pointsList = util.getStrings(util.removeFirstLastCurlBrackets(shapeList[8]))
      for point in pointsList:
        linePoints = util.getStrings(util.removeFirstLastCurlBrackets(point))
        points.append([float(linePoints[0]), float(linePoints[1])])
      graphicsObject["points"] = points
      minX = 100
      minY = 100
      maxX = -100
      maxY = -100

      for point in graphicsObject["points"]:
        if minX > point[0]:
          minX = point[0]
        if maxX < point[0]:
          maxX = point[0]
        if minY > point[1]:
          minY = point[1]
        if maxY < point[1]:
          maxY = point[1]

      graphicsObject["extent"] = [[minX, minY], [maxX, maxY]]
      # 10th item of list contains the smooth.
      graphicsObject["smooth"] = shapeList[9]
    elif shape.startswith("Text"):
      graphicsObject["type"] = "Text"
      shape = shape[len("Text"):]
      shapeList = util.getStrings(util.removeFirstLastParentheses(shape))
      util.parseGraphicItem(graphicsObject, shapeList)
      util.parseFilledShape(graphicsObject, shapeList)
      # 9th item is the extent points.
      extentsList = util.getStrings(util.removeFirstLastCurlBrackets(shapeList[8]))
      extentPoints1 = util.getStrings(util.removeFirstLastCurlBrackets(extentsList[0]))
      extentPoints2 = util.getStrings(util.removeFirstLastCurlBrackets(extentsList[1]))
      graphicsObject["extent"] = [[float(extentPoints1[0]), float(extentPoints1[1])], [float(extentPoints2[0]), float(extentPoints2[1])]]
      # 10th item of the list contains the textString.
      if shapeList[9].startswith("{"): # DynamicSelect
        args = util.getStrings(util.removeFirstLastCurlBrackets(shapeList[9]))
        graphicsObject["textString"] = args[0].strip('"')
      else:
        graphicsObject["textString"] = shapeList[9].strip('"')
      # 11th item of the list contains the fontSize.
      graphicsObject["fontSize"] = float(shapeList[10])
      # 12th item of the list contains the optional textColor, {-1, -1, -1} if not set
      colorList = util.getStrings(util.removeFirstLastCurlBrackets(shapeList[11]))
      graphicsObject["textColor"] = [int(colorList[0]), int(colorList[1]), int(colorList[2])]
      # 13th item of the list contains the font name.
      graphicsObject["fontName"] = shapeList[12].strip('"')
      # 14th item of the list contains the text styles.
      graphicsObject["textStyle"] = util.getStrings(util.removeFirstLastCurlBrackets(shapeList[13]))
      # 15th item of the list contains the text alignment.
      graphicsObject["horizontalAlignment"] = shapeList[14]
    elif shape.startswith("Ellipse"):
      graphicsObject["type"] = "Ellipse"
      shape = shape[len("Ellipse"):]
      shapeList = util.getStrings(util.removeFirstLastParentheses(shape))
      util.parseGraphicItem(graphicsObject, shapeList)
      util.parseFilledShape(graphicsObject, shapeList)
      # 9th item is the extent points.
      extentsList = util.getStrings(util.removeFirstLastCurlBrackets(shapeList[8]))
      extentPoints1 = util.getStrings(util.removeFirstLastCurlBrackets(extentsList[0]))
      extentPoints2 = util.getStrings(util.removeFirstLastCurlBrackets(extentsList[1]))
      graphicsObject["extent"] = [[float(extentPoints1[0]), float(extentPoints1[1])], [float(extentPoints2[0]), float(extentPoints2[1])]]
      # 10th item of the list contains the start angle.
      graphicsObject["startAngle"] = float(shapeList[9])
      # 11th item of the list contains the end angle.
      graphicsObject["endAngle"] = float(shapeList[10])
    elif shape.startswith("Bitmap"):
      graphicsObject["type"] = "Bitmap"
      shape = shape[len("Bitmap"):]
      shapeList = util.getStrings(util.removeFirstLastParentheses(shape))
      util.parseGraphicItem(graphicsObject, shapeList)
      # 4th item is the extent points
      extentsList = util.getStrings(util.removeFirstLastCurlBrackets(shapeList[3]))
      extentPoints1 = util.getStrings(util.removeFirstLastCurlBrackets(extentsList[0]))
      extentPoints2 = util.getStrings(util.removeFirstLastCurlBrackets(extentsList[1]))
      graphicsObject["extent"] = [[float(extentPoints1[0]), float(extentPoints1[1])], [float(extentPoints2[0]), float(extentPoints2[1])]]
      # 5th item is the fileName
      # 6th item is the imageSource
      if len(shapeList) >= 6:
        graphicsObject["href"] = "data:image;base64,"+shapeList[5].strip('"')
      else:
        fileName = sendCommand("uriToFilename({0})".format(shapeList[4]), parsed=False).strip().strip('"')
        if not os.path.exists(fileName):
          fileName = os.path.join(baseDir, shapeList[4].strip('"'))
        if os.path.exists(fileName):
          with open(fileName, "rb") as fileD:
            graphicsObject["href"] = "data:image;base64,"+str(base64.b64encode(fileD.read()))
        else:
          log.error("Could not find bitmap file %s", shapeList[4])
          graphicsObject["href"] = shapeList[4].strip('"')

    classGraphics["graphics"].append(graphicsObject)

  return classGraphics
