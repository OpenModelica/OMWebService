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
from OMPython import OMCSessionZMQ
import re

log = logging.getLogger(__name__)
omc = OMCSessionZMQ()

def sendCommand(expression, parsed=True):
  log.debug('sendCommand: {0} - parsed: {1}'.format(expression, parsed))

  try:
    res = omc.sendExpression(expression, parsed)
    log.debug("OMC getErrorString(): {0}".format(omc.sendExpression("getErrorString()")))
  except Exception as e:
    log.error("OMC failed: {0}, parsed={1} with exception: {2}".format(expression, parsed, str(e)))
    raise

  return res

def pythonBoolToModelicaBool(value):
  if value:
    return "true"
  else:
    return "false"

if not sendCommand('loadModel(Modelica)', True):
  log.critical('Failed to load Modelica standard library: {0}'.format(omc.sendExpression('getErrorString()')))

def wordsBeforeAfterLastDot(value, lastWord):
  if not value:
    return ""

  value = value.strip()
  pos = 0
  if value.endswith('\''):
    i = len(value) - 2
    while value[i] != '\'' and i > 1 and value[i-1] != '\\':
      i -= 1

    pos = i - 1
  else:
    pos = value.rfind('.')

  if pos >= 0:
    if lastWord:
      return value[pos+1:len(value)]
    else:
      return value[0:pos]
  else:
    return value

def getLastWordAfterDot(value):
  return wordsBeforeAfterLastDot(value, True)

# Note: The order of the base classes matters
def getBaseClasses(className, baseClasses):
  inheritanceCount = sendCommand("getInheritanceCount({0})".format(className))

  for i in range(1, inheritanceCount + 1):
    baseClass = sendCommand("getNthInheritedClass({0}, {1})".format(className ,str(i)))
    if baseClass not in baseClasses:
      baseClasses.append(baseClass)
      getBaseClasses(baseClass, baseClasses)

# get graphics objects from annotation Icon
def getClassGraphics(className):

  exp_float = '[+-]?\d+(?:.\d+)?(?:e[+-]?\d+)?'
  # Compile regular expressions ONLY once!
  # example: {-100.0,-100.0,100.0,100.0,true,0.16,2.0,2.0, {...
  regexCoOrdinateSystem = re.compile('('+exp_float+'),('+exp_float+'),('+exp_float+'),('+exp_float+'),(\w+),('+exp_float+'),('+exp_float+'),('+exp_float+'),')

  # example: Rectangle(true, {35.0, 10.0}, 0, {0, 0, 0}, {255, 255, 255}, LinePattern.Solid, FillPattern.Solid, 0.25, BorderPattern.None, {{-15.0, -4.0}, {15.0, 4.0}}, 0
  regexRectangle = re.compile('Rectangle\(([\w ]+), {('+exp_float+'), ('+exp_float+')}, ('+exp_float+'), {(\d+), (\d+), (\d+)}, {(\d+), (\d+), (\d+)}, (\w+.\w+), (\w+.\w+), ('+exp_float+'), (\w+.\w+), {{('+exp_float+'), ('+exp_float+')}, {('+exp_float+'), ('+exp_float+')}}, ('+exp_float+')')

  # example: Line(true, {0.0, 0.0}, 0, {{-30, -120}, {-10, -100}}, {0, 0, 0}, LinePattern.Solid, 0.25, {Arrow.None, Arrow.None}, 3, Smooth.None
  regexLine = re.compile('Line\(([\w ]+), {('+exp_float+'), ('+exp_float+')}, ('+exp_float+'), ({{'+exp_float+', '+exp_float+'}(?:, {'+exp_float+', '+exp_float+'})*}), {(\d+), (\d+), (\d+)}, (\w+.\w+), ('+exp_float+'), {(\w+.\w+), (\w+.\w+)}, ('+exp_float+'), (\w+.\w+)')

  # example: Ellipse(true, {0.0, 0.0}, 0, {0, 0, 0}, {95, 95, 95}, LinePattern.Solid, FillPattern.Solid, 0.25, {{-100, 100}, {100, -100}}, 0, 360)}}
  regexEllipse = re.compile('Ellipse\(([\w ]+), {('+exp_float+'), ('+exp_float+')}, ('+exp_float+'), {(\d+), (\d+), (\d+)}, {(\d+), (\d+), (\d+)}, (\w+.\w+), (\w+.\w+), ('+exp_float+'), {{('+exp_float+'), ('+exp_float+')}, {('+exp_float+'), ('+exp_float+')}}, ('+exp_float+'), ('+exp_float+')')

  # example: Text(true, {0.0, 0.0}, 0, {0, 0, 255}, {0, 0, 0}, LinePattern.Solid, FillPattern.None, 0.25, {{-150, 110}, {150, 70}}, "%name", 0, {-1, -1, -1}, "fontName", {TextStyle.Bold, TextStyle.Italic, TextStyle.UnderLine}, TextAlignment.Center
  regexText = re.compile('Text\(([\w ]+), {('+exp_float+'), ('+exp_float+')}, ('+exp_float+'), {(\d+), (\d+), (\d+)}, {(\d+), (\d+), (\d+)}, (\w+.\w+), (\w+.\w+), ('+exp_float+'), {{('+exp_float+'), ('+exp_float+')}, {('+exp_float+'), ('+exp_float+')}}, ("[^"]*"), ('+exp_float+'), {([+-]?\d+), ([+-]?\d+), ([+-]?\d+)}, ("[^"]*"), {([^}]*)}, (\w+.\w+)')

  # example: Text(true, {0.0, 0.0}, 0, {0, 0, 255}, {0, 0, 0}, LinePattern.Solid, FillPattern.None, 0.25, {{-150, 110}, {150, 70}}, {"%name", y, 0}, 0, {-1, -1, -1}, "fontName", {TextStyle.Bold, TextStyle.Italic, TextStyle.UnderLine}, TextAlignment.Center
  regexText2 = re.compile('Text\(([\w ]+), {('+exp_float+'), ('+exp_float+')}, ('+exp_float+'), {(\d+), (\d+), (\d+)}, {(\d+), (\d+), (\d+)}, (\w+.\w+), (\w+.\w+), ('+exp_float+'), {{('+exp_float+'), ('+exp_float+')}, {('+exp_float+'), ('+exp_float+')}}, {("[^"]*"), [+-, \w\d]*}, ('+exp_float+'), {([+-]?\d+), ([+-]?\d+), ([+-]?\d+)}, ("[^"]*"), {([^}]*)}, (\w+.\w+)')

  # example: Polygon(true, {0.0, 0.0}, 0, {0, 127, 255}, {0, 127, 255}, LinePattern.Solid, FillPattern.Solid, 0.25, {{-24, -34}, {-82, 40}, {-72, 46}, {-14, -26}, {-24, -34}}, Smooth.None
  #   Polygon(true, {-60, -40},90, {0, 0, 0}, {255, 128, 0}, LinePattern.Solid, FillPattern.VerticalCylinder, 0.25, {{-20.0, 10.0}, {0.0, -10.0}, {1.22465e-16, -50.0}, {-10.0, -60.0}, {-20.0, -60.0}, {-20.0, 10.0}}, Smooth.None
  regexPolygon = re.compile('Polygon\(([\w ]+), {('+exp_float+'), ('+exp_float+')}, ('+exp_float+'), {(\d+), (\d+), (\d+)}, {(\d+), (\d+), (\d+)}, (\w+.\w+), (\w+.\w+), ('+exp_float+'), ({{'+exp_float+'(?:e[+-]?\d+)?, '+exp_float+'(?:e[+-]?\d+)?}(?:, {'+exp_float+', '+exp_float+'})*}), (\w+.\w+)')

  # example: {{-100.0, -100.0}, {-100.0, -30.0}, {0.0, -30.0}, {0.0, 0.0}}
  regexPoints = re.compile('{('+exp_float+'), ('+exp_float+')}')

  # example: Bitmap(true, {0.0, 0.0}, 0, {{-98, 98}, {98, -98}}, "modelica://Modelica/Resources/Images/Mechanics/MultiBody/Visualizers/TorusIcon.png"
  regexBitmap = re.compile('Bitmap\(([\w ]+), {('+exp_float+'), ('+exp_float+')}, ('+exp_float+'), {{('+exp_float+'), ('+exp_float+')}, {('+exp_float+'), ('+exp_float+')}}, ("[^"]*")(?:, ("[^"]*"))?')

  # anything unknown that produces output should look like this: Trash(...
  regexAny = re.compile('(\w+)\(')

  iconAnnotation = sendCommand("getIconAnnotation({0})".format(className), parsed=False)

  classGraphics = dict()
  classGraphics['graphics'] = []
  classGraphics['coordinateSystem'] = {}
  classGraphics['coordinateSystem']['extent'] = [[-100, -100], [100, 100]]

  shapes = ""
  shape = regexCoOrdinateSystem.search(iconAnnotation)
  if shape:
    g = shape.groups()
    classGraphics['coordinateSystem']['extent'] = [[float(g[0]), float(g[1])], [float(g[2]), float(g[3])]]
    classGraphics['coordinateSystem']['preserveAspectRatio'] = bool(g[4])
    classGraphics['coordinateSystem']['initialScale'] = float(g[5])
    classGraphics['coordinateSystem']['grid'] = [float(g[6]), float(g[7])]

    shapes = iconAnnotation[iconAnnotation.find(',{'):]
  else:
    shapes = iconAnnotation

  for shape in shapes.split('),'):
    # default values
    graphicsObject = {}

    r = regexLine.search(shape)
    if r:
      graphicsObject['type'] = 'Line'
      g = r.groups()
      graphicsObject['visible'] = g[0]
      graphicsObject['origin'] = [float(g[1]), float(g[2])]
      graphicsObject['rotation'] = float(g[3])

      points = []
      gg = re.findall(regexPoints, g[4])
      for i in range(0, len(gg)):
        points.append([float(gg[i][0]), float(gg[i][1])])
      graphicsObject['points'] = points

      graphicsObject['color'] = [int(g[5]), int(g[6]), int(g[7])]
      graphicsObject['pattern'] = g[8]
      graphicsObject['thickness'] = float(g[9])
      graphicsObject['arrow'] = [g[10], g[11]]
      graphicsObject['arrowSize'] = float(g[12])
      graphicsObject['smooth'] = g[13]

    r = regexRectangle.search(shape)
    if r:
      graphicsObject['type'] = 'Rectangle'
      g = r.groups()
      graphicsObject['visible'] = g[0]
      graphicsObject['origin'] = [float(g[1]), float(g[2])]
      graphicsObject['rotation'] = float(g[3])
      graphicsObject['lineColor'] = [int(g[4]), int(g[5]), int(g[6])]
      graphicsObject['fillColor'] = [int(g[7]), int(g[8]), int(g[9])]
      graphicsObject['linePattern'] = g[10]
      graphicsObject['fillPattern'] = g[11]
      graphicsObject['lineThickness'] = float(g[12])
      graphicsObject['borderPattern'] = g[13]
      graphicsObject['extent'] = [[float(g[14]), float(g[15])], [float(g[16]), float(g[17])]]
      graphicsObject['radius'] = float(g[18])

    r = regexPolygon.search(shape)
    if r:
      graphicsObject['type'] = 'Polygon'
      g = r.groups()
      graphicsObject['visible'] = g[0]
      graphicsObject['origin'] = [float(g[1]), float(g[2])]
      graphicsObject['rotation'] = float(g[3])
      graphicsObject['lineColor'] = [int(g[4]), int(g[5]), int(g[6])]
      graphicsObject['fillColor'] = [int(g[7]), int(g[8]), int(g[9])]
      graphicsObject['linePattern'] = g[10]
      graphicsObject['fillPattern'] = g[11]
      graphicsObject['lineThickness'] = float(g[12])

      points = []
      gg = re.findall(regexPoints, g[13])
      for i in range(0, len(gg)):
        points.append([float(gg[i][0]), float(gg[i][1])])
      graphicsObject['points'] = points

      minX = 100
      minY = 100
      maxX = -100
      maxY = -100

      for point in graphicsObject['points']:
        if minX > point[0]:
          minX = point[0]
        if maxX < point[0]:
          maxX = point[0]
        if minY > point[1]:
          minY = point[1]
        if maxY < point[1]:
          maxY = point[1]

      graphicsObject['extent'] = [[minX, minY], [maxX, maxY]]
      graphicsObject['smooth'] = g[14]

    r = regexText.search(shape)
    if not r:
      r = regexText2.search(shape)
    if r:
      graphicsObject['type'] = 'Text'
      g = r.groups()
      graphicsObject['visible'] = g[0]
      graphicsObject['origin'] = [float(g[1]), float(g[2])]
      graphicsObject['rotation'] = float(g[3])
      graphicsObject['lineColor'] = [int(g[4]), int(g[5]), int(g[6])]
      graphicsObject['fillColor'] = [int(g[7]), int(g[8]), int(g[9])]
      graphicsObject['linePattern'] = g[10]
      graphicsObject['fillPattern'] = g[11]
      graphicsObject['lineThickness'] = float(g[12])
      graphicsObject['extent'] = [[float(g[13]), float(g[14])], [float(g[15]), float(g[16])]]
      graphicsObject['textString'] = g[17].strip('"')
      graphicsObject['fontSize'] = float(g[18])
      graphicsObject['textColor'] = [int(g[19]), int(g[20]), int(g[21])]
      graphicsObject['fontName'] = g[22]
      if graphicsObject['fontName']:
        graphicsObject['fontName'] = graphicsObject['fontName'].strip('"')

      graphicsObject['textStyle'] = []
      if g[23]:
        graphicsObject['textStyle'] = regex_type_value.findall(g[23])  # text Style can have different number of styles

      graphicsObject['horizontalAlignment'] = g[24]

    r = regexEllipse.search(shape)
    if r:
      g = r.groups()
      graphicsObject['type'] = 'Ellipse'
      graphicsObject['visible'] = g[0]
      graphicsObject['origin'] = [float(g[1]), float(g[2])]
      graphicsObject['rotation'] = float(g[3])
      graphicsObject['lineColor'] = [int(g[4]), int(g[5]), int(g[6])]
      graphicsObject['fillColor'] = [int(g[7]), int(g[8]), int(g[9])]
      graphicsObject['linePattern'] = g[10]
      graphicsObject['fillPattern'] = g[11]
      graphicsObject['lineThickness'] = float(g[12])
      graphicsObject['extent'] = [[float(g[13]), float(g[14])], [float(g[15]), float(g[16])]]
      graphicsObject['startAngle'] = float(g[17])
      graphicsObject['endAngle'] = float(g[18])

    r = regexBitmap.search(shape)
    if r:
      g = r.groups()
      graphicsObject['type'] = 'Bitmap'
      graphicsObject['visible'] = g[0]
      graphicsObject['origin'] = [float(g[1]), float(g[2])]
      graphicsObject['rotation'] = float(g[3])
      graphicsObject['extent'] = [[float(g[4]), float(g[5])], [float(g[6]), float(g[7])]]
      if g[9] is not None:
        graphicsObject['href'] = "data:image;base64,"+g[9].strip('"')
      else:
        fname = omcproxy.sendCommand("uriToFilename({0})".format(g[8]), parsed=False).strip().strip('"')
        if not os.path.exists(fname):
          fname = os.path.join(baseDir, g[8].strip('"'))
        if os.path.exists(fname):
          with open(fname, "rb") as f_p:
            graphicsObject['href'] = "data:image;base64,"+str(base64.b64encode(f_p.read()))
        else:
          log.error("Could not find bitmap file {0}".format(g[8]))
          graphicsObject['href'] = g[8].strip('"')

    if not 'type' in graphicsObject:
      r = regexAny.search(shape)
      if r:
        g = r.groups()
        graphicsObject['type'] = 'Unknown'
        log.error('Unknown graphicsObject: {0}'.format(g[0]))
      elif shape.strip() == '{}': # ignore empty icons
        graphicsObject['type'] = 'Empty'
      else: # assume others to be empty as well
        graphicsObject['type'] = 'Empty'
        log.info('Treating graphicsObject as empty icon: {0}'.format(shape))

    classGraphics['graphics'].append(graphicsObject)

  return classGraphics
