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
__status__ = "Prototype"
__maintainer__ = "https://openmodelica.org"

import os
import re
import math
import json
import logging
import sys
import time
import base64
import datetime
from optparse import OptionParser
from enum import Enum

from OMPython import OMCSessionZMQ
omc = OMCSessionZMQ()

def classToFileName(cl):
  """
  The file-system dislikes directory separators, and scripts dislike tokens that expand to other names.
  This function uses the same replacement rules as the OpenModelica documentation-generating script.
  """
  return cl.replace("/","Division").replace("*","Multiplication").replace("<","x3C").replace(">","x3E")

exp_float = '[+-]?\d+(?:.\d+)?(?:e[+-]?\d+)?'

element_id = 0
regex_equal_key_value = re.compile("([^ =]+) *= *(\"[^\"]*\"|[^ ]*)")

regex_type_value = re.compile("(\w+.\w+)*")

# Compile regular expressions ONLY once!
# example: {-100.0,-100.0,100.0,100.0,true,0.16,2.0,2.0, {...
regex_coordSys = re.compile('('+exp_float+'),('+exp_float+'),('+exp_float+'),('+exp_float+'),(\w+),('+exp_float+'),('+exp_float+'),('+exp_float+'),')

# example: Rectangle(true, {35.0, 10.0}, 0, {0, 0, 0}, {255, 255, 255}, LinePattern.Solid, FillPattern.Solid, 0.25, BorderPattern.None, {{-15.0, -4.0}, {15.0, 4.0}}, 0
regex_rectangle = re.compile('Rectangle\(([\w ]+), {('+exp_float+'), ('+exp_float+')}, ('+exp_float+'), {(\d+), (\d+), (\d+)}, {(\d+), (\d+), (\d+)}, (\w+.\w+), (\w+.\w+), ('+exp_float+'), (\w+.\w+), {{('+exp_float+'), ('+exp_float+')}, {('+exp_float+'), ('+exp_float+')}}, ('+exp_float+')')

# example: Line(true, {0.0, 0.0}, 0, {{-30, -120}, {-10, -100}}, {0, 0, 0}, LinePattern.Solid, 0.25, {Arrow.None, Arrow.None}, 3, Smooth.None
regex_line = re.compile('Line\(([\w ]+), {('+exp_float+'), ('+exp_float+')}, ('+exp_float+'), ({{'+exp_float+', '+exp_float+'}(?:, {'+exp_float+', '+exp_float+'})*}), {(\d+), (\d+), (\d+)}, (\w+.\w+), ('+exp_float+'), {(\w+.\w+), (\w+.\w+)}, ('+exp_float+'), (\w+.\w+)')

# example: Ellipse(true, {0.0, 0.0}, 0, {0, 0, 0}, {95, 95, 95}, LinePattern.Solid, FillPattern.Solid, 0.25, {{-100, 100}, {100, -100}}, 0, 360)}}
regex_ellipse = re.compile('Ellipse\(([\w ]+), {('+exp_float+'), ('+exp_float+')}, ('+exp_float+'), {(\d+), (\d+), (\d+)}, {(\d+), (\d+), (\d+)}, (\w+.\w+), (\w+.\w+), ('+exp_float+'), {{('+exp_float+'), ('+exp_float+')}, {('+exp_float+'), ('+exp_float+')}}, ('+exp_float+'), ('+exp_float+')')

# example: Text(true, {0.0, 0.0}, 0, {0, 0, 255}, {0, 0, 0}, LinePattern.Solid, FillPattern.None, 0.25, {{-150, 110}, {150, 70}}, "%name", 0, {-1, -1, -1}, "fontName", {TextStyle.Bold, TextStyle.Italic, TextStyle.UnderLine}, TextAlignment.Center
regex_text = re.compile('Text\(([\w ]+), {('+exp_float+'), ('+exp_float+')}, ('+exp_float+'), {(\d+), (\d+), (\d+)}, {(\d+), (\d+), (\d+)}, (\w+.\w+), (\w+.\w+), ('+exp_float+'), {{('+exp_float+'), ('+exp_float+')}, {('+exp_float+'), ('+exp_float+')}}, ("[^"]*"), ('+exp_float+'), {([+-]?\d+), ([+-]?\d+), ([+-]?\d+)}, ("[^"]*"), {([^}]*)}, (\w+.\w+)')

# example: Text(true, {0.0, 0.0}, 0, {0, 0, 255}, {0, 0, 0}, LinePattern.Solid, FillPattern.None, 0.25, {{-150, 110}, {150, 70}}, {"%name", y, 0}, 0, {-1, -1, -1}, "fontName", {TextStyle.Bold, TextStyle.Italic, TextStyle.UnderLine}, TextAlignment.Center
regex_text2 = re.compile('Text\(([\w ]+), {('+exp_float+'), ('+exp_float+')}, ('+exp_float+'), {(\d+), (\d+), (\d+)}, {(\d+), (\d+), (\d+)}, (\w+.\w+), (\w+.\w+), ('+exp_float+'), {{('+exp_float+'), ('+exp_float+')}, {('+exp_float+'), ('+exp_float+')}}, {("[^"]*"), [+-, \w\d]*}, ('+exp_float+'), {([+-]?\d+), ([+-]?\d+), ([+-]?\d+)}, ("[^"]*"), {([^}]*)}, (\w+.\w+)')

# example: Polygon(true, {0.0, 0.0}, 0, {0, 127, 255}, {0, 127, 255}, LinePattern.Solid, FillPattern.Solid, 0.25, {{-24, -34}, {-82, 40}, {-72, 46}, {-14, -26}, {-24, -34}}, Smooth.None
#   Polygon(true, {-60, -40},90, {0, 0, 0}, {255, 128, 0}, LinePattern.Solid, FillPattern.VerticalCylinder, 0.25, {{-20.0, 10.0}, {0.0, -10.0}, {1.22465e-16, -50.0}, {-10.0, -60.0}, {-20.0, -60.0}, {-20.0, 10.0}}, Smooth.None
regex_polygon = re.compile('Polygon\(([\w ]+), {('+exp_float+'), ('+exp_float+')}, ('+exp_float+'), {(\d+), (\d+), (\d+)}, {(\d+), (\d+), (\d+)}, (\w+.\w+), (\w+.\w+), ('+exp_float+'), ({{'+exp_float+'(?:e[+-]?\d+)?, '+exp_float+'(?:e[+-]?\d+)?}(?:, {'+exp_float+', '+exp_float+'})*}), (\w+.\w+)')

# example: {{-100.0, -100.0}, {-100.0, -30.0}, {0.0, -30.0}, {0.0, 0.0}}
regex_points = re.compile('{('+exp_float+'), ('+exp_float+')}')

# example: Bitmap(true, {0.0, 0.0}, 0, {{-98, 98}, {98, -98}}, "modelica://Modelica/Resources/Images/Mechanics/MultiBody/Visualizers/TorusIcon.png"
# TODO: where is the imageSource?
regex_bitmap = re.compile('Bitmap\(([\w ]+), {('+exp_float+'), ('+exp_float+')}, ('+exp_float+'), {{('+exp_float+'), ('+exp_float+')}, {('+exp_float+'), ('+exp_float+')}}, ("[^"]*")(?:, ("[^"]*"))?')

# anything unknown that produces output should look like this: Trash(...
regex_any = re.compile('(\w+)\(')

omc_cache = {}

def ask_omc(question, opt=None, parsed=True):
  p = (question, opt, parsed)
  if p in omc_cache:
    return omc_cache[p]

  if opt:
    expression = question + '(' + opt + ')'
  else:
    expression = question

  logger.debug('ask_omc: {0}  - parsed: {1}'.format(expression, parsed))

  try:
    if parsed:
      res = omc.execute(expression)
    else:
      res = omc.sendExpression(expression, parsed=False)
  except Exception as e:
    logger.error("OMC failed: {0}, {1}, parsed={2}".format(question, opt, parsed))
    raise

  omc_cache[p] = res

  return res

class ViewType(Enum):
  icon=1
  diagram=2

def getAnnotation(modelicaClass, viewType):
  result = dict()

  if viewType == ViewType.icon:
    annotation = ask_omc('getIconAnnotation', modelicaClass, parsed=False)
  elif viewType == ViewType.diagram:
    annotation = ask_omc('getDiagramAnnotation', modelicaClass, parsed=False)

  result['coordinateSystem'] = {}
  result['coordinateSystem']['extent'] = [[-100, -100], [100, 100]]

  r = regex_coordSys.search(annotation)
  if r:
    g = r.groups()
    result['coordinateSystem']['extent'] = [[float(g[0]), float(g[1])], [float(g[2]), float(g[3])]]
    result['coordinateSystem']['preserveAspectRatio'] = bool(g[4])
    result['coordinateSystem']['initialScale'] = float(g[5])
    result['coordinateSystem']['grid'] = [float(g[6]), float(g[7])]

    withOutCoordSys = annotation[annotation.find(',{'):]
  else:
    # logger.warning('Coordinate system was skipped')
    # logger.warning(answer2)
    withOutCoordSys = annotation

  result['shapes'] = []
  for shapes in withOutCoordSys.split('),'):

    # default values
    graphicsObj = {}

    r = regex_line.search(shapes)
    if r:
      graphicsObj['type'] = 'Line'
      g = r.groups()
      graphicsObj['visible'] = g[0]
      graphicsObj['origin'] = [float(g[1]), float(g[2])]
      graphicsObj['rotation'] = float(g[3])

      points = []
      gg = re.findall(regex_points, g[4])
      for i in range(0, len(gg)):
          points.append([float(gg[i][0]), float(gg[i][1])])
      graphicsObj['points'] = points

      graphicsObj['color'] = [int(g[5]), int(g[6]), int(g[7])]
      graphicsObj['pattern'] = g[8]
      graphicsObj['thickness'] = float(g[9])
      graphicsObj['arrow'] = [g[10], g[11]]
      graphicsObj['arrowSize'] = float(g[12])
      graphicsObj['smooth'] = g[13]

    r = regex_rectangle.search(shapes)
    if r:
      graphicsObj['type'] = 'Rectangle'
      g = r.groups()
      graphicsObj['visible'] = g[0]
      graphicsObj['origin'] = [float(g[1]), float(g[2])]
      graphicsObj['rotation'] = float(g[3])
      graphicsObj['lineColor'] = [int(g[4]), int(g[5]), int(g[6])]
      graphicsObj['fillColor'] = [int(g[7]), int(g[8]), int(g[9])]
      graphicsObj['linePattern'] = g[10]
      graphicsObj['fillPattern'] = g[11]
      graphicsObj['lineThickness'] = float(g[12])
      graphicsObj['borderPattern'] = g[13]
      graphicsObj['extent'] = [[float(g[14]), float(g[15])], [float(g[16]), float(g[17])]]
      graphicsObj['radius'] = float(g[18])

    r = regex_polygon.search(shapes)
    if r:
      graphicsObj['icon_line'] = shapes
      graphicsObj['type'] = 'Polygon'
      g = r.groups()
      graphicsObj['visible'] = g[0]
      graphicsObj['origin'] = [float(g[1]), float(g[2])]
      graphicsObj['rotation'] = float(g[3])
      graphicsObj['lineColor'] = [int(g[4]), int(g[5]), int(g[6])]
      graphicsObj['fillColor'] = [int(g[7]), int(g[8]), int(g[9])]
      graphicsObj['linePattern'] = g[10]
      graphicsObj['fillPattern'] = g[11]
      graphicsObj['lineThickness'] = float(g[12])

      points = []
      gg = re.findall(regex_points, g[13])
      for i in range(0, len(gg)):
        points.append([float(gg[i][0]), float(gg[i][1])])
      graphicsObj['points'] = points

      minX = 100
      minY = 100
      maxX = -100
      maxY = -100

      for point in graphicsObj['points']:
        if minX > point[0]:
          minX = point[0]
        if maxX < point[0]:
          maxX = point[0]
        if minY > point[1]:
          minY = point[1]
        if maxY < point[1]:
          maxY = point[1]

      graphicsObj['extent'] = [[minX, minY], [maxX, maxY]]

      graphicsObj['smooth'] = g[14]

    r = regex_text.search(shapes)
    if not r:
      r = regex_text2.search(shapes)
    if r:
      graphicsObj['type'] = 'Text'
      g = r.groups()
      graphicsObj['visible'] = g[0]
      graphicsObj['origin'] = [float(g[1]), float(g[2])]
      graphicsObj['rotation'] = float(g[3])
      graphicsObj['lineColor'] = [int(g[4]), int(g[5]), int(g[6])]
      graphicsObj['fillColor'] = [int(g[7]), int(g[8]), int(g[9])]
      graphicsObj['linePattern'] = g[10]
      graphicsObj['fillPattern'] = g[11]
      graphicsObj['lineThickness'] = float(g[12])
      graphicsObj['extent'] = [[float(g[13]), float(g[14])], [float(g[15]), float(g[16])]]
      graphicsObj['textString'] = g[17].strip('"')
      graphicsObj['fontSize'] = float(g[18])
      graphicsObj['textColor'] = [int(g[19]), int(g[20]), int(g[21])]
      graphicsObj['fontName'] = g[22]
      if graphicsObj['fontName']:
        graphicsObj['fontName'] = graphicsObj['fontName'].strip('"')

      graphicsObj['textStyle'] = []
      if g[23]:
        graphicsObj['textStyle'] = regex_type_value.findall(g[23])  # text Style can have different number of styles

      graphicsObj['horizontalAlignment'] = g[24]

    r = regex_ellipse.search(shapes)
    if r:
      g = r.groups()
      graphicsObj['type'] = 'Ellipse'
      graphicsObj['visible'] = g[0]
      graphicsObj['origin'] = [float(g[1]), float(g[2])]
      graphicsObj['rotation'] = float(g[3])
      graphicsObj['lineColor'] = [int(g[4]), int(g[5]), int(g[6])]
      graphicsObj['fillColor'] = [int(g[7]), int(g[8]), int(g[9])]
      graphicsObj['linePattern'] = g[10]
      graphicsObj['fillPattern'] = g[11]
      graphicsObj['lineThickness'] = float(g[12])
      graphicsObj['extent'] = [[float(g[13]), float(g[14])], [float(g[15]), float(g[16])]]
      graphicsObj['startAngle'] = float(g[17])
      graphicsObj['endAngle'] = float(g[18])

    r = regex_bitmap.search(shapes)
    if r:
      g = r.groups()
      graphicsObj['type'] = 'Bitmap'
      graphicsObj['visible'] = g[0]
      graphicsObj['origin'] = [float(g[1]), float(g[2])]
      graphicsObj['rotation'] = float(g[3])
      graphicsObj['extent'] = [[float(g[4]), float(g[5])], [float(g[6]), float(g[7])]]
      if g[9] is not None:
        graphicsObj['href'] = "data:image;base64,"+g[9].strip('"')
      else:
        fname = ask_omc('uriToFilename', g[8], parsed=False).strip().strip('"')
        if not os.path.exists(fname):
          fname = os.path.join(baseDir, g[8].strip('"'))
        if os.path.exists(fname):
          with open(fname, "rb") as f_p:
              graphicsObj['href'] = "data:image;base64,"+str(base64.b64encode(f_p.read()))
        else:
          logger.error("Could not find bitmap file {0}".format(g[8]))
          graphicsObj['href'] = g[8].strip('"')

    if not 'type' in graphicsObj:
      r = regex_any.search(shapes)
      if r:
        g = r.groups()
        graphicsObj['type'] = 'Unknown'
        logger.error('Unknown graphicsObj: {0}'.format(g[0]))
      else: # ignore empty icons and assume others to be empty as well
        logger.info('Treating graphicsObj as empty : {0}'.format(shapes))

    if not len(graphicsObj) == 0:
      result['shapes'].append(graphicsObj)

  return result

def removeFirstLastCurlBrackets(value):
  value = value.strip()
  if (len(value) > 1 and value[0] == '{' and value[len(value) - 1] == '}'):
    value = value[1: len(value) - 1]
  return value

def unparseArrays(value):
  lst = []
  braceopen = 0
  mainbraceopen = 0
  i = 0
  value = removeFirstLastCurlBrackets(value)
  length = len(value)
  subbraceopen = 0

  while i < len(value):
    if value[i] == ' ' or value[i] == ',':
      i+=1
      continue # ignore any kind of space
    if value[i] == '{' and braceopen == 0:
      braceopen = 1
      mainbraceopen = i
      i+=1
      continue
    if value[i] == '{':
      subbraceopen = 1

    if value[i] == '}' and braceopen == 1 and subbraceopen == 0:
      # closing of a group
      braceopen = 0
      lst.append(value[mainbraceopen:i+1])
      i+=1
      continue
    if value[i] == '}':
      subbraceopen = 0

    # skip the whole quotes section
    if value[i] == '"':
      i+=1
      while value[i] != '"':
        i+=1
        if value[i-1] == '\\' and value[i] == '"':
          i+=1

    i+=1

  return lst

def consumeChar(value, res, i):
  if value[i] == '\\':
    i+=1
    if (value[i] == '\''):
      res.append('\'')
    elif (value[i] == '"'):
      res.append('\"')
    elif (value[i] == '?'):
      res.append('\?')
    elif (value[i] == '\\'):
      res.append('\\')
    elif (value[i] == 'a'):
      res.append('\a')
    elif (value[i] == 'b'):
      res.append('\b')
    elif (value[i] == 'f'):
      res.append('\f')
    elif (value[i] == 'n'):
      res.append('\n')
    elif (value[i] == 'r'):
      res.append('\r')
    elif (value[i] == 't'):
      res.append('\t')
    elif (value[i] == 'v'):
      res.append('\v')
  else:
    res.append(value[i])
  
  return res

def unparseStrings(value):
  lst = []
  value = value.strip()
  if value[0] != '{':
    return lst #ERROR?
  i = 1
  res = []
  while value[i] == '"':
    i+=1
    while value[i] != '"':
      res = consumeChar(value, res, i)
      i+=1
      # if we have unexpected double quotes then, however omc should return \"
      # remove this block once fixed in omc
      if value[i] == '"' and value[i+1] != ',':
        if value[i+1] != '}':
          res = consumeChar(value, res, i)
          i+=1
      # remove this block once fixed in omc
    i+=1
    if value[i] == '}':
      lst.append(''.join(res))
      return lst
    if value[i] == ',':
      lst.append(''.join(res))
      i+=1
      res = []
      while value[i] == ' ': # if we have space before next value e.g {"x", "y", "z"}
        i+=1
      continue
    while value[i] != '"' and value[i] is not None:
      i+=1
      print("error? malformed string-list. skipping: %c" % value[i])
  
  return lst

def getStrings(value, start='{', end='}'):
  lst = []
  mask = False
  inString = False
  stringEnd = '\0'
  begin = 0
  ele = 0

  for i in range(len(value)):
    if inString:
      if mask:
        mask = False
      else:
        if value[i] == '\\':
          mask = True
        elif value[i] == stringEnd:
          inString = False
    else:
      if value[i] == '"':
        stringEnd = '"'
        inString = True
      elif value[i] == '\'':
        stringEnd = '\''
        inString = True
      elif value[i] == ',':
        if ele == 0:
          lst.append(value[begin:i].strip())
          begin = i+1
      elif value[i] == start:
        ele+=1
      elif value[i] == end:
        ele-=1

  lst.append(value[begin:len(value) + 1].strip())
  return lst

def getElements(modelicaClass, parameters, connectors):
  components = ask_omc('getComponents', modelicaClass + ', useQuotes = true', parsed=False)
  componentsList = unparseArrays(components)
  if componentsList:
    componentAnnotations = ask_omc('getComponentAnnotations', modelicaClass, parsed=False)
    componentAnnotationsList = getStrings(removeFirstLastCurlBrackets(componentAnnotations))

    for i in range(len(componentsList)):
      try:
        componentInfo = unparseStrings(componentsList[i])
        if ask_omc('isConnector', componentInfo[0]):
          element = dict()
          element['info'] = componentInfo
          element['annotation'] = componentAnnotationsList[i]
          connectors.append(element)
        elif (componentInfo[8] == 'parameter'):
          element = dict()
          element['info'] = componentInfo
          element['annotation'] = componentAnnotationsList[i]
          parameters.append(element)
      except KeyError as ex:
        logger.error('KeyError: {0} index: {1} {2}'.format(modelicaClass, i+1, str(ex)))
        continue

  inheritedClassesJsonList = []
  inheritedClasses = getInheritedClasses(modelicaClass)
  for inheritedClass in inheritedClasses:
    if inheritedClass:
      getElements(inheritedClass, parameters, connectors)

def getConnections(modelicaClass):
  return []

def getInheritedClasses(modelicaClass):
  return getStrings(removeFirstLastCurlBrackets(ask_omc('getInheritedClasses', modelicaClass, parsed=False)))

def exportJson(modelicaClass, topLevel = False):
  classJson = dict()

  classInfo  = omc.sendExpression('getClassInformation({0})'.format(modelicaClass))
  baseDir = os.path.dirname(classInfo[5])

  classJson['className'] = modelicaClass
  if topLevel:
    classJson['svgPath'] = "svg/" + classToFileName(modelicaClass) + ".svg"
  classJson['info'] = classInfo
  #classJson['icon'] = getAnnotation(modelicaClass, ViewType.icon)
  #classJson['diagram'] = getAnnotation(modelicaClass, ViewType.diagram)
  parameters = []
  connectors = []
  getElements(modelicaClass, parameters, connectors)
  classJson['connectors'] = connectors
  classJson['parameters'] = parameters
  classJson['connections'] = getConnections(modelicaClass)

  return classJson

def main():
  global baseDir
  t = time.time()
  parser = OptionParser()
  parser.add_option("--className", help="Modelica class name", type="string", dest="className", default="")
  parser.add_option("--output-dir", help="Directory to generate json file in", type="string", dest="output_dir", default=os.path.abspath('IconsJson'))
  parser.add_option("--quiet", help="Do not output to the console", action="store_true", dest="quiet", default=False)
  (options, args) = parser.parse_args()
  className = options.className
  if not className:
    parser.print_help()
    return
  global output_dir
  output_dir = options.output_dir

  # create logger with 'spam_application'
  global logger
  logger = logging.getLogger(os.path.basename(__file__))
  logger.setLevel(logging.DEBUG)

  # create console handler with a higher log level
  ch = logging.StreamHandler()
  if not options.quiet:
    ch.setLevel(logging.INFO)
  else:
    ch.setLevel(logging.CRITICAL)

  # create formatter and add it to the handlers
  formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
  ch.setFormatter(formatter)

  # add the handlers to the logger
  logger.addHandler(ch)

  logger.info('Application started')
  logger.info('Output directory: ' + output_dir)

  if not os.path.exists(output_dir):
    try:
      os.makedirs(output_dir)
    except:
      pass

  logger.info('Loading Modelica')
  package_load = omc.sendExpression('loadModel(Modelica)')
  if not package_load:
    logger.critical('Failed to load Modelica standard library in %.1f seconds: %s' % (time.time()-t,omc.sendExpression('getErrorString()')))
    return 1
  
  try:
    # create file handler which logs even debug messages
    fh = logging.FileHandler(className + '.log')
    fh.setLevel(logging.DEBUG)
    fh.setFormatter(formatter)
    logger.addHandler(fh)

    logger.info('Exporting: ' + className)

    classJson = exportJson(className, True)
    with open(os.path.join(output_dir, classToFileName(className) + '.json'), 'w') as f_p:
      json.dump(classJson, f_p, indent=2)

    logger.info('Done: ' + className)
    # except:
    #     print 'FAILED: ' + className
    logger.removeHandler(fh)
  except Exception as e:
    logger.critical('Failed to generate json for %s after %.1f seconds: %s' % (className,time.time()-t,sys.exc_info()[1]))
    raise

  print("%s Generated json for %s in %.1f seconds" % (datetime.datetime.now(),className,time.time()-t))

  logger.info('End of application')
  return 0

if __name__ == '__main__':
  sys.exit(main())

