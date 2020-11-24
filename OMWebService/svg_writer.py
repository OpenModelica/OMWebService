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
Creates the svg using the graphics representation of a class.
"""

import logging
import math
import svgwrite

log = logging.getLogger(__name__)

def getGradientColors(startColor, stopColor, midPoints):
  """Generates the gradient colors."""
  result = []

  startRed = int(startColor[0])
  startGreen = int(startColor[1])
  startBlue = int(startColor[2])

  stopRed = int(stopColor[0])
  stopGreen = int(stopColor[1])
  stopBlue = int(stopColor[2])

  rDelta = (stopRed - startRed) / (midPoints + 1)
  gDelta = (stopGreen - startGreen) / (midPoints + 1)
  bDelta = (stopBlue - startBlue) / (midPoints + 1)

  result.append((startRed, startGreen, startBlue))

  for i in range(1, midPoints + 1):
    result.append((startRed + i * rDelta, startGreen + i * gDelta, startBlue + i * bDelta))

  result.append((stopRed, stopGreen, stopBlue))

  return result

def getCoordinates(xyValue, graphics, minX, maxY, transformation, coordinateSystem):
  """Gets the coordinates from the transformation and coordinate system."""
  xValue = xyValue[0] + graphics["origin"][0]
  yValue = xyValue[1] + graphics["origin"][1]

  # rotation for the icon
  sinRotation = math.sin(graphics["rotation"] / 180 * 3.1415)
  cosRotation = math.cos(graphics["rotation"] / 180 * 3.1415)

  xValue -= graphics["origin"][0]
  yValue -= graphics["origin"][1]

  xnew = xValue * cosRotation - yValue * sinRotation
  ynew = xValue * sinRotation + yValue * cosRotation

  xValue = xnew + graphics["origin"][0]
  yValue = ynew + graphics["origin"][1]

  if transformation and coordinateSystem:
    try:
      tWidth = abs(max(transformation["extent"][1][0], transformation["extent"][0][0]) - min(transformation["extent"][1][0], transformation["extent"][0][0]))
      tHeight = abs(max(transformation["extent"][1][1], transformation["extent"][0][1]) - min(transformation["extent"][1][1], transformation["extent"][0][1]))
      oWidth = abs(max(coordinateSystem["extent"][1][0], coordinateSystem["extent"][0][0]) - min(coordinateSystem["extent"][1][1], coordinateSystem["extent"][0][1]))
      oHeight = abs(max(coordinateSystem["extent"][1][1], coordinateSystem["extent"][0][1]) - min(coordinateSystem["extent"][1][1], coordinateSystem["extent"][0][1]))

      if "extent" in transformation and transformation["extent"][1][0] < transformation["extent"][0][0]:
        # horizontal flip
        xValue = (-xyValue[0] + graphics["origin"][0]) / oWidth * tWidth + transformation["origin"][0] + transformation["extent"][1][0] + tWidth / 2
      else:
        xValue = (xyValue[0] + graphics["origin"][0]) / oWidth * tWidth + transformation["origin"][0] + transformation["extent"][0][0] + tWidth / 2

      if "extent" in transformation and transformation["extent"][1][1] < transformation["extent"][0][1]:
        # vertical flip
        yValue = (-xyValue[1] + graphics["origin"][1]) / oHeight * tHeight + transformation["origin"][1] + min(transformation["extent"][1][1], transformation["extent"][0][1]) + tHeight / 2
      else:
        yValue = (xyValue[1] + graphics["origin"][1]) / oHeight * tHeight + transformation["origin"][1] + min(transformation["extent"][0][1], transformation["extent"][0][1]) + tHeight / 2

      sinRotation = math.sin(transformation["rotation"] / 180 * 3.1415)
      cosRotation = math.cos(transformation["rotation"] / 180 * 3.1415)

      xValue -= transformation["origin"][0]
      yValue -= transformation["origin"][1]

      xnew = xValue * cosRotation - yValue * sinRotation
      ynew = xValue * sinRotation + yValue * cosRotation

      xValue = xnew + transformation["origin"][0]
      yValue = ynew + transformation["origin"][1]

    except KeyError as ex:
      log.error("Component position transformation failed to get the key: %s", str(ex))
      log.error(graphics)

  xValue -= minX
  yValue = maxY - yValue

  return xValue, yValue

def getShapeSvgFromGraphics(dwg, graphics, minX, maxY, elementId, transformation=None, coordinateSystem=None):
  """Creats the svg shape from graphics."""
  shape = None
  definitions = svgwrite.container.Defs()

  if not "origin" in graphics:
    graphics["origin"] = (0, 0)

  if graphics["type"] == "Rectangle" or graphics["type"] == "Ellipse" or graphics["type"] == "Text" or graphics["type"] == "Bitmap":
    (xValue0, yValue0) = getCoordinates(graphics["extent"][0], graphics, minX, maxY, transformation, coordinateSystem)
    (xValue1, yValue1) = getCoordinates(graphics["extent"][1], graphics, minX, maxY, transformation, coordinateSystem)

  if graphics["type"] == "Rectangle" or graphics["type"] == "Ellipse" or graphics["type"] == "Polygon":
    if not "fillPattern" in graphics:
      graphics["fillPattern"] = "FillPattern.None"

  if graphics["type"] == "Rectangle":
    shape = dwg.rect((min(xValue0, xValue1), min(yValue0, yValue1)), (abs(xValue1 - xValue0), abs(yValue1 - yValue0)), graphics["rotation"], graphics["rotation"])

  elif graphics["type"] == "Line":
    if "points" in graphics:
      if graphics["smooth"] == "Smooth.Bezier" and len(graphics["points"]) > 2:
        # Optimize this part!!!
        shape = svgwrite.path.Path()
        xValue0, yValue0 = getCoordinates([graphics["points"][0][0], graphics["points"][0][1]], graphics, minX, maxY, transformation, coordinateSystem)
        shape.push("M", xValue0, yValue0, "C")

        for i in range(1, len(graphics["points"]) - 1):
          xValue0, yValue0 = getCoordinates([graphics["points"][i-1][0], graphics["points"][i-1][1]], graphics, minX, maxY, transformation, coordinateSystem)
          xCoordinate1, yCoordinate1 = getCoordinates([graphics["points"][i][0], graphics["points"][i][1]], graphics, minX, maxY, transformation, coordinateSystem)
          xCoordinate2, yCoordinate2 = getCoordinates([graphics["points"][i+1][0], graphics["points"][i+1][1]], graphics, minX, maxY, transformation, coordinateSystem)
          xCoordinate01 = (xCoordinate1 + xValue0) / 2
          yCoordinate01 = (yCoordinate1 + yValue0) / 2
          xCoordinate12 = (xCoordinate2 + xCoordinate1) / 2
          yCoordinate12 = (yCoordinate2 + yCoordinate1) / 2
          shape.push(xCoordinate01, yCoordinate01, xCoordinate1, yCoordinate1, xCoordinate12, yCoordinate12)
        xCoordinate, yCoordinate = getCoordinates([graphics["points"][len(graphics["points"]) - 1][0], graphics["points"][len(graphics["points"]) - 1][1]], graphics, minX, maxY, transformation, coordinateSystem)
        shape.push(xCoordinate12, yCoordinate12, xCoordinate, yCoordinate, xCoordinate, yCoordinate)
      else:
        shape = dwg.polyline([getCoordinates([xValue, yValue], graphics, minX, maxY, transformation, coordinateSystem) for (xValue, yValue) in graphics["points"]])
      shape.fill("none", opacity=0)

      # markers
      if graphics["arrow"][0] != "Arrow.None":
        urlIdStart = graphics["arrow"][0] + "_start" + str(elementId)
        elementId += 1
        marker = svgwrite.container.Marker(insert=(10, 5), size=(4, 3), orient="auto", id=urlIdStart, viewBox="0 0 10 10")
        path = svgwrite.path.Path(d="M 10 0 L 0 5 L 10 10 z")
        path.fill("rgb(" + ",".join([str(v) for v in graphics["color"]]) + ")")
        marker.add(path)
        definitions.add(marker)
        shape["marker-start"] = marker.get_funciri()

      if graphics["arrow"][1] != "Arrow.None":
        urlIdEnd = graphics["arrow"][1] + "_end" + str(elementId)
        elementId += 1
        marker = svgwrite.container.Marker(insert=(0, 5), size=(4, 3), orient="auto", id=urlIdEnd, viewBox="0 0 10 10")
        path = svgwrite.path.Path(d="M 0 0 L 10 5 L 0 10 z")
        path.fill("rgb(" + ",".join([str(v) for v in graphics["color"]]) + ")")
        marker.add(path)
        definitions.add(marker)
        shape["marker-end"] = marker.get_funciri()

    else:
      log.error("Not handled: %s", graphics)
      return None

  elif graphics["type"] == "Polygon":
    if "points" in graphics:
      if graphics["smooth"] == "Smooth.Bezier" and len(graphics["points"]) > 2:
        # Optimize this part!!!
        shape = svgwrite.path.Path()
        xValue0, yValue0 = getCoordinates([graphics["points"][0][0], graphics["points"][0][1]], graphics, minX, maxY, transformation, coordinateSystem)
        shape.push("M", xValue0, yValue0, "C")

        for i in range(1, len(graphics["points"]) - 1):
          xValue0, yValue0 = getCoordinates([graphics["points"][i-1][0], graphics["points"][i-1][1]], graphics, minX, maxY, transformation, coordinateSystem)
          xCoordinate1, yCoordinate1 = getCoordinates([graphics["points"][i][0], graphics["points"][i][1]], graphics, minX, maxY, transformation, coordinateSystem)
          xCoordinate2, yCoordinate2 = getCoordinates([graphics["points"][i+1][0], graphics["points"][i+1][1]], graphics, minX, maxY, transformation, coordinateSystem)
          xCoordinate01 = (xCoordinate1 + xValue0) / 2
          yCoordinate01 = (yCoordinate1 + yValue0) / 2
          xCoordinate12 = (xCoordinate2 + xCoordinate1) / 2
          yCoordinate12 = (yCoordinate2 + yCoordinate1) / 2
          shape.push(xCoordinate01, yCoordinate01, xCoordinate1, yCoordinate1, xCoordinate12, yCoordinate12)
        xCoordinate, yCoordinate = getCoordinates([graphics["points"][len(graphics["points"]) - 1][0], graphics["points"][len(graphics["points"]) - 1][1]], graphics, minX, maxY, transformation, coordinateSystem)
        shape.push(xCoordinate12, yCoordinate12, xCoordinate, yCoordinate, xCoordinate, yCoordinate)
      else:
        shape = dwg.polygon([getCoordinates([xValue, yValue], graphics, minX, maxY, transformation, coordinateSystem) for (xValue, yValue) in graphics["points"]])
      shape.fill("none", opacity=0)
    else:
      log.error("Not handled: %s", graphics)
      return None

  elif graphics["type"] == "Ellipse":
    shape = dwg.ellipse(((xValue0 + xValue1) / 2, (yValue0 + yValue1) / 2), (abs((xValue1 - xValue0) / 2), abs((yValue1 - yValue0) / 2)))

  elif graphics["type"] == "Text":
    extra = {}
    xValue = (xValue0 + xValue1) / 2
    yValue = (yValue0 + yValue1) / 2

    extra["font_family"] = graphics["fontName"] or "Verdana"

    if graphics["fontSize"] == 0:
      extra["font_size"] = str(abs(yValue1-yValue0)) # fit text into extent according to 18.6.5.5
    else:
      extra["font_size"] = graphics["fontSize"]

    for style in graphics["textStyle"]:
      if style == "TextStyle.Bold":
        extra["font-weight"] = "bold"
      elif style == "TextStyle.Italic":
        extra["font-style"] = "italic"
      elif style == "TextStyle.UnderLine":
        extra["text-decoration"] = "underline"

    extra["dominant_baseline"] = "middle"

    if graphics["horizontalAlignment"] == "TextAlignment.Left":
      extra["text_anchor"] = "start"
      if xValue0 < xValue1:
        xValue = xValue0
      else:
        xValue = xValue1
      if yValue0 < yValue1:
        yValue = yValue0
      else:
        yValue = yValue1
    elif graphics["horizontalAlignment"] == "TextAlignment.Center":
      extra["text_anchor"] = "middle"
    elif graphics["horizontalAlignment"] == "TextAlignment.Right":
      extra["text_anchor"] = "end"
      if xValue0 < xValue1:
        xValue = xValue1
      else:
        xValue = xValue0
      if yValue0 < yValue1:
        yValue = yValue1
      else:
        yValue = yValue0

    shape = dwg.text(graphics["textString"], None, [xValue], [yValue], **extra)

  elif graphics["type"] == "Bitmap":
    xmin = xValue0
    ymin = yValue0
    xmax = xValue1
    ymax = yValue1

    if xValue0 > xValue1:
      xmin = xValue1
      xmax = xValue0
    if yValue0 > yValue1:
      ymin = yValue1
      ymax = yValue0
    shape = dwg.image(graphics["href"], x=xmin,y=ymin,width=xmax-xmin,height=ymax-ymin) # put in correct URL or base64 data "data:image;base64,"

  elif graphics["type"] == "Empty":
    return None

  else:
    log.warning("Not handled: %s", graphics)
    return None

  dotSize = 4
  dashSize = 16
  spaceSize = 8

  if "linePattern" in graphics:
    dotSize *= graphics["lineThickness"]
    dashSize *= graphics["lineThickness"]
    spaceSize *= graphics["lineThickness"]

    if graphics["linePattern"] == "LinePattern.None" or graphics["type"] == "Text":
      pass
    elif graphics["linePattern"] == "LinePattern.Solid":
      shape.stroke("rgb(" + ",".join([str(v) for v in graphics["lineColor"]]) + ")", width="{0}mm".format(graphics["lineThickness"]))
    elif graphics["linePattern"] == "LinePattern.Dash":
      shape.stroke("rgb(" + ",".join([str(v) for v in graphics["lineColor"]]) + ")", width="{0}mm".format(graphics["lineThickness"]))
      shape.dasharray([dashSize, spaceSize])
    elif graphics["linePattern"] == "LinePattern.Dot":
      shape.stroke("rgb(" + ",".join([str(v) for v in graphics["lineColor"]]) + ")", width="{0}mm".format(graphics["lineThickness"]))
      shape.dasharray([dotSize, spaceSize])
    elif graphics["linePattern"] == "LinePattern.DashDot":
      shape.stroke("rgb(" + ",".join([str(v) for v in graphics["lineColor"]]) + ")", width="{0}mm".format(graphics["lineThickness"]))
      shape.dasharray([dashSize, spaceSize, dotSize, spaceSize])
    elif graphics["linePattern"] == "LinePattern.DashDotDot":
      shape.stroke("rgb(" + ",".join([str(v) for v in graphics["lineColor"]]) + ")", width="{0}mm".format(graphics["lineThickness"]))
      shape.dasharray([dashSize, spaceSize, dotSize, spaceSize, dotSize, spaceSize])

    if graphics["type"] == "Rectangle":
      if graphics["borderPattern"] == "BorderPattern.None":
        pass
      elif graphics["borderPattern"] == "BorderPattern.Raised":
        urlId = graphics["borderPattern"] + "_" + str(elementId)
        elementId += 1
        shape["filter"] = "url(#" + urlId + ")"

        svgFilter = svgwrite.filters.Filter(id=urlId, filterUnits="objectBoundingBox", x="-0.1", y="-0.1", width="1.2", height="1.2")
        svgFilter.feGaussianBlur("SourceAlpha", stdDeviation="5", result="alpha_blur")
        feSL = svgFilter.feSpecularLighting("alpha_blur", surfaceScale="5", specularConstant="1", specularExponent="20", lighting_color="#FFFFFF", result="spec_light")
        feSL.fePointLight((-5000, -10000, 10000))
        svgFilter.feComposite("spec_light", in2="SourceAlpha", operator="in", result="spec_light")
        svgFilter.feComposite("SourceGraphic", in2="spec_light", operator="out", result="spec_light_fill")

        definitions.add(svgFilter)
      elif graphics["borderPattern"] == "BorderPattern.Sunken":
        log.warning("Not supported: %s", graphics["borderPattern"])
      elif graphics["borderPattern"] == "BorderPattern.Engraved":
        log.warning("Not supported: %s", graphics["borderPattern"])

  if "color" in graphics:
    try:
      shape.stroke("rgb(" + ",".join([str(v) for v in graphics["color"]]) + ")", width="{0}mm".format(graphics["thickness"]))
    except TypeError as ex:
      log.error("%s %s", graphics["color"], str(ex))

  if "pattern" in graphics:
    dotSize *= graphics["thickness"]
    dashSize *= graphics["thickness"]
    spaceSize *= graphics["thickness"]

    if graphics["pattern"] == "LinePattern.None" or graphics["type"] == "Text":
      pass
    elif graphics["pattern"] == "LinePattern.Solid":
      shape.stroke("rgb(" + ",".join([str(v) for v in graphics["color"]]) + ")", width="{0}mm".format(graphics["thickness"]))
    elif graphics["pattern"] == "LinePattern.Dash":
      shape.stroke("rgb(" + ",".join([str(v) for v in graphics["color"]]) + ")", width="{0}mm".format(graphics["thickness"]))
      shape.dasharray([dashSize, spaceSize])
    elif graphics["pattern"] == "LinePattern.Dot":
      shape.stroke("rgb(" + ",".join([str(v) for v in graphics["color"]]) + ")", width="{0}mm".format(graphics["thickness"]))
      shape.dasharray([dotSize, spaceSize])
    elif graphics["pattern"] == "LinePattern.DashDot":
      shape.stroke("rgb(" + ",".join([str(v) for v in graphics["color"]]) + ")", width="{0}mm".format(graphics["thickness"]))
      shape.dasharray([dashSize, spaceSize, dotSize, spaceSize])
    elif graphics["pattern"] == "LinePattern.DashDotDot":
      shape.stroke("rgb(" + ",".join([str(v) for v in graphics["color"]]) + ")", width="{0}mm".format(graphics["thickness"]))
      shape.dasharray([dashSize, spaceSize, dotSize, spaceSize, dotSize, spaceSize])

  if "fillPattern" in graphics:
    if graphics["fillPattern"] == "FillPattern.None":
      if graphics["type"] == "Text":
        shape.fill("rgb(" + ",".join([str(v) for v in graphics["lineColor"]]) + ")", opacity=1)
      else:
        shape.fill("none", opacity=0)
    elif graphics["fillPattern"] == "FillPattern.Solid":
      shape.fill("rgb(" + ",".join([str(v) for v in graphics["fillColor"]]) + ")", opacity=1)
    elif graphics["fillPattern"] == "FillPattern.Horizontal":
      urlId = str(elementId)
      elementId += 1
      shape.fill("url(#" + urlId + ")")

      pattern = svgwrite.pattern.Pattern(id=urlId, insert=(0, 0), size=(5, 5), patternUnits="userSpaceOnUse")

      rect = svgwrite.shapes.Rect(insert=(0, 0), size=(5, 5))
      rect.fill("rgb(" + ",".join([str(v) for v in graphics["fillColor"]]) + ")")
      pattern.add(rect)

      svgPath = svgwrite.path.Path(d="M0,0 L5,0")
      svgPath.stroke("rgb(" + ",".join([str(v) for v in graphics["lineColor"]]) + ")", width=2)
      pattern.add(svgPath)

      definitions.add(pattern)

    elif graphics["fillPattern"] == "FillPattern.Vertical":
      urlId = str(elementId)
      elementId += 1
      shape.fill("url(#" + urlId + ")")

      pattern = svgwrite.pattern.Pattern(id=urlId, insert=(0, 0), size=(5, 5), patternUnits="userSpaceOnUse")

      rect = svgwrite.shapes.Rect(insert=(0, 0), size=(5, 5))
      rect.fill("rgb(" + ",".join([str(v) for v in graphics["fillColor"]]) + ")")
      pattern.add(rect)

      svgPath = svgwrite.path.Path(d="M0,0 L0,5")
      svgPath.stroke("rgb(" + ",".join([str(v) for v in graphics["lineColor"]]) + ")", width=2)
      pattern.add(svgPath)

      definitions.add(pattern)

    elif graphics["fillPattern"] == "FillPattern.Cross":
      urlId = str(elementId)
      elementId += 1
      shape.fill("url(#" + urlId + ")")

      pattern = svgwrite.pattern.Pattern(id=urlId, insert=(0, 0), size=(5, 5), patternUnits="userSpaceOnUse")

      rect = svgwrite.shapes.Rect(insert=(0, 0), size=(5, 5))
      rect.fill("rgb(" + ",".join([str(v) for v in graphics["fillColor"]]) + ")")
      pattern.add(rect)

      svgPath = svgwrite.path.Path(d="M0,0 L5,0")
      svgPath.stroke("rgb(" + ",".join([str(v) for v in graphics["lineColor"]]) + ")", width=2)
      pattern.add(svgPath)

      svgPath = svgwrite.path.Path(d="M0,0 L0,5")
      svgPath.stroke("rgb(" + ",".join([str(v) for v in graphics["lineColor"]]) + ")", width=2)
      pattern.add(svgPath)

      definitions.add(pattern)

    elif graphics["fillPattern"] == "FillPattern.Forward":
      urlId = str(elementId)
      elementId += 1
      shape.fill("url(#" + urlId + ")")

      pattern = svgwrite.pattern.Pattern(id=urlId, insert=(0, 0), size=(7, 7), patternUnits="userSpaceOnUse")

      rect = svgwrite.shapes.Rect(insert=(0, 0), size=(7, 7))
      rect.fill("rgb(" + ",".join([str(v) for v in graphics["fillColor"]]) + ")")
      pattern.add(rect)

      svgPath = svgwrite.path.Path(d="M0,0 l7,7")
      svgPath.stroke("rgb(" + ",".join([str(v) for v in graphics["lineColor"]]) + ")", width=1)
      pattern.add(svgPath)

      svgPath = svgwrite.path.Path(d="M6,-1 l3,3")
      svgPath.stroke("rgb(" + ",".join([str(v) for v in graphics["lineColor"]]) + ")", width=1)
      pattern.add(svgPath)

      svgPath = svgwrite.path.Path(d="M-1,6 l3,3")
      svgPath.stroke("rgb(" + ",".join([str(v) for v in graphics["lineColor"]]) + ")", width=1)
      pattern.add(svgPath)

      definitions.add(pattern)

    elif graphics["fillPattern"] == "FillPattern.Backward":
      urlId = str(elementId)
      elementId += 1
      shape.fill("url(#" + urlId + ")")

      pattern = svgwrite.pattern.Pattern(id=urlId, insert=(0, 0), size=(7, 7), patternUnits="userSpaceOnUse")

      rect = svgwrite.shapes.Rect(insert=(0, 0), size=(7, 7))
      rect.fill("rgb(" + ",".join([str(v) for v in graphics["fillColor"]]) + ")")
      pattern.add(rect)

      svgPath = svgwrite.path.Path(d="M7,0 l-7,7")
      svgPath.stroke("rgb(" + ",".join([str(v) for v in graphics["lineColor"]]) + ")", width=1)
      pattern.add(svgPath)

      svgPath = svgwrite.path.Path(d="M1,-1 l-7,7")
      svgPath.stroke("rgb(" + ",".join([str(v) for v in graphics["lineColor"]]) + ")", width=1)
      pattern.add(svgPath)

      svgPath = svgwrite.path.Path(d="M8,6 l-7,7")
      svgPath.stroke("rgb(" + ",".join([str(v) for v in graphics["lineColor"]]) + ")", width=1)
      pattern.add(svgPath)

      definitions.add(pattern)

    elif graphics["fillPattern"] == "FillPattern.CrossDiag":

      urlId = str(elementId)
      elementId += 1
      shape.fill("url(#" + urlId + ")")

      pattern = svgwrite.pattern.Pattern(id=urlId, insert=(0, 0), size=(8, 8), patternUnits="userSpaceOnUse")

      rect = svgwrite.shapes.Rect(insert=(0, 0), size=(8, 8))
      rect.fill("rgb(" + ",".join([str(v) for v in graphics["fillColor"]]) + ")")
      pattern.add(rect)

      svgPath = svgwrite.path.Path(d="M0,0 l8,8")
      svgPath.stroke("rgb(" + ",".join([str(v) for v in graphics["lineColor"]]) + ")", width=1)
      pattern.add(svgPath)

      svgPath = svgwrite.path.Path(d="M8,0 l-8,8")
      svgPath.stroke("rgb(" + ",".join([str(v) for v in graphics["lineColor"]]) + ")", width=1)
      pattern.add(svgPath)

      definitions.add(pattern)

    elif graphics["fillPattern"] == "FillPattern.HorizontalCylinder":

      urlId = str(elementId)
      elementId += 1
      shape.fill("url(#" + urlId + ")")

      lineColor = graphics["lineColor"]
      fillColor = graphics["fillColor"]

      if not lineColor:
        lineColor = "black"
      if not fillColor:
        fillColor = "white"

      gradient = svgwrite.gradients.LinearGradient(id=urlId, x1="0%", y1="0%", x2="0%", y2="100%")

      colors = getGradientColors(lineColor, fillColor, 0)

      stopValues = [
        (0, 0),
        (0.3, 1),
        (0.7, 1),
        (1, 0)
      ]

      for (stopValue, idx) in stopValues:
        gradient.add_stop_color(offset=stopValue, color="rgb({0}, {1}, {2})".format(colors[idx][0], colors[idx][1], colors[idx][2]), opacity=1)

      definitions.add(gradient)

    elif graphics["fillPattern"] == "FillPattern.VerticalCylinder":
      urlId = str(elementId)
      elementId += 1
      shape.fill("url(#" + urlId + ")")

      lineColor = graphics["lineColor"]
      fillColor = graphics["fillColor"]

      if not lineColor:
        lineColor = "black"
      if not fillColor:
        fillColor = "white"

      gradient = svgwrite.gradients.LinearGradient(id=urlId, x1="0%", y1="0%", x2="100%", y2="0%")

      colors = getGradientColors(lineColor, fillColor, 0)

      stopValues = [
        (0, 0),
        (0.3, 1),
        (0.7, 1),
        (1, 0)
      ]

      for (stopValue, idx) in stopValues:
        gradient.add_stop_color(offset=stopValue, color="rgb({0}, {1}, {2})".format(colors[idx][0], colors[idx][1], colors[idx][2]), opacity=1)

      definitions.add(gradient)
    elif graphics["fillPattern"] == "FillPattern.Sphere":
      if graphics["type"] == "Ellipse":
        urlId = str(elementId)
        elementId += 1

        shape.fill("url(#" + urlId + ")")

        lineColor = graphics["lineColor"]
        fillColor = graphics["fillColor"]

        if not lineColor:
          lineColor = "black"
        if not fillColor:
          fillColor = "white"

        gradient = svgwrite.gradients.RadialGradient(id=urlId, cx="50%", cy="50%", r="55%", fx="50%", fy="50%")
        colors = getGradientColors(lineColor, fillColor, 9)

        stopValues = [
          (0, 10),
          (0.45, 8),
          (0.7, 6),
          (1, 0)
        ]

        for (stopValue, idx) in stopValues:
          gradient.add_stop_color(offset=stopValue, color="rgb({0}, {1}, {2})".format(int(colors[idx][0]), int(colors[idx][1]), int(colors[idx][2])), opacity=1)

        definitions.add(gradient)
      elif graphics["type"] == "Rectangle":
        urlId = str(elementId)
        elementId += 1

        shape.fill("url(#" + urlId + ")")

        lineColor = graphics["lineColor"]
        fillColor = graphics["fillColor"]

        if not lineColor:
          lineColor = "black"
        if not fillColor:
          fillColor = "white"

        gradient = svgwrite.gradients.RadialGradient(id=urlId, cx="50%", cy="50%", r="0.9", fx="50%", fy="50%")

        colors = getGradientColors(lineColor, fillColor, 0)

        stopValues = [
          (0, 1),
          (1, 0)
        ]

        for (stopValue, idx) in stopValues:
          gradient.add_stop_color(offset=stopValue, color="rgb({0}, {1}, {2})".format(colors[idx][0], colors[idx][1], colors[idx][2]), opacity=1)

        definitions.add(gradient)
  else:
    if graphics["type"] != "Bitmap":
      shape.fill("none", opacity=0)
  return shape, definitions

def writeSVG(fileName, iconGraphics):
  """Writes a SVG to a file."""
  elementId = 0
  width = 100
  height = 100

  minX = 0
  minY = 0
  maxX = 100
  maxY = 100

  for iconGraphic in iconGraphics:
    for graphics in iconGraphic["graphics"]:

      if not "origin" in graphics:
        graphics["origin"] = (0, 0)

      if not "extent" in graphics:
        graphics["extent"] = [[-100, -100], [100, 100]]

      if "extent" in graphics:
        minX = min(minX, graphics["extent"][0][0] + graphics["origin"][0])
        minX = min(minX, graphics["extent"][1][0] + graphics["origin"][0])
        minY = min(minY, graphics["extent"][0][1] + graphics["origin"][1])
        minY = min(minY, graphics["extent"][1][1] + graphics["origin"][1])
        maxX = max(maxX, graphics["extent"][1][0] + graphics["origin"][0])
        maxX = max(maxX, graphics["extent"][0][0] + graphics["origin"][0])
        maxY = max(maxY, graphics["extent"][1][1] + graphics["origin"][1])
        maxY = max(maxY, graphics["extent"][0][1] + graphics["origin"][1])

      if "points" in graphics:
        for point in graphics["points"]:
          minX = min(minX, point[0] + graphics["origin"][0])
          minY = min(minY, point[1] + graphics["origin"][1])
          maxX = max(maxX, point[0] + graphics["origin"][0])
          maxX = max(maxY, point[1] + graphics["origin"][1])

  width = maxX - minX
  height = maxY - minY

  dwg = svgwrite.Drawing(fileName, size=(width, height), viewBox="0 0 " + str(width) + " " + str(height))

  for iconGraphic in iconGraphics:
    for graphics in iconGraphic["graphics"]:
      svgShape = getShapeSvgFromGraphics(dwg, graphics, minX, maxY, elementId)
      if svgShape:
        dwg.add(svgShape[0])
        dwg.add(svgShape[1])

  dwg.save(pretty=True)
  return width, height
