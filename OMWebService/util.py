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
Module containing helper functions.
"""

def pythonBoolToModelicaBool(value):
  """Converts the python bool to Modelica."""
  if value:
    return "true"
  else:
    return "false"

def wordsBeforeAfterLastDot(value, lastWord):
  """Returns the word before or after dot."""
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
  """Returns the last word after dot."""
  return wordsBeforeAfterLastDot(value, True)

def removeFirstLastCurlBrackets(value):
  """Removes the first and last curl bracket."""
  value = value.strip()
  if (len(value) > 1 and value[0] == '{' and value[len(value) - 1] == '}'):
    value = value[1: len(value) - 1]
  return value

def removeFirstLastParentheses(value):
  """Removes the first and last parentheses."""
  value = value.strip()
  if (len(value) > 1 and value[0] == '(' and value[len(value) - 1] == ')'):
    value = value[1: len(value) - 1]
  return value

def unparseArrays(value):
  """Returns the list of arrays."""
  lst = []
  braceopen = 0
  mainbraceopen = 0
  i = 0
  value = removeFirstLastCurlBrackets(value)
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
  """Escapes the characters for use."""
  if value[i] == '\\':
    i+=1
    if value[i] == '\'':
      res.append('\'')
    elif value[i] == '"':
      res.append('\"')
    elif value[i] == '?':
      res.append(r'\?')
    elif value[i] == '\\':
      res.append('\\')
    elif value[i] == 'a':
      res.append('\a')
    elif value[i] == 'b':
      res.append('\b')
    elif value[i] == 'f':
      res.append('\f')
    elif value[i] == 'n':
      res.append('\n')
    elif value[i] == 'r':
      res.append('\r')
    elif value[i] == 't':
      res.append('\t')
    elif value[i] == 'v':
      res.append('\v')
  else:
    res.append(value[i])

  return res, i

def unparseStrings(value):
  """Returns the list of strings."""
  lst = []
  value = value.strip()
  if value[0] != '{':
    return lst #ERROR?
  i = 1
  res = []
  while value[i] == '"':
    i+=1
    while value[i] != '"':
      (res, i) = consumeChar(value, res, i)
      i+=1
      # if we have unexpected double quotes then, however omc should return \"
      # remove this block once fixed in omc
      if value[i] == '"' and value[i+1] != ',':
        if value[i+1] != '}':
          (res, i) = consumeChar(value, res, i)
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
  """Returns the list of strings."""
  lst = []
  mask = False
  inString = False
  stringEnd = '\0'
  begin = 0
  ele = 0

  for i, val in enumerate(value):
    if inString:
      if mask:
        mask = False
      else:
        if val == '\\':
          mask = True
        elif val == stringEnd:
          inString = False
    else:
      if val == '"':
        stringEnd = '"'
        inString = True
      elif val == '\'':
        stringEnd = '\''
        inString = True
      elif val == ',':
        if ele == 0:
          lst.append(value[begin:i].strip())
          begin = i+1
      elif val == start:
        ele+=1
      elif val == end:
        ele-=1

  lst.append(value[begin:len(value) + 1].strip())
  return lst

def componentPlacement(componentAnnotations):
  """Creates a placement dictionary from component annotation."""
  placement = dict()
  componentAnnotations = removeFirstLastCurlBrackets(componentAnnotations)
  annotations = getStrings(componentAnnotations, "(", ")")
  for annotation in annotations:
    if annotation.startswith("Placement"):
      annotation = annotation[len("Placement"):]
      placementAnnotation = removeFirstLastParentheses(annotation)
      if placementAnnotation.lower() == "error":
        return placement
      else:
        placementAnnotation = getStrings(placementAnnotation)
        placement["origin"] = {"x": placementAnnotation[1], "y": placementAnnotation[2]}
        placement["bottomLeft"] = {"x": placementAnnotation[3], "y": placementAnnotation[4]}
        placement["topRight"] = {"x": placementAnnotation[5], "y": placementAnnotation[6]}
        placement["rotation"] = placementAnnotation[7]
        return placement
  return placement

def svgJson(path, width, height):
  """Creates a svg json dictionary from svg attributes."""
  json = dict()
  json["path"] = path
  json["width"] = width
  json["height"] = height
  return json

def parseGraphicItem(graphicsObject, shapeList):
  """Parses the Graphics item annotation."""
  # 1st item is the visible
  if shapeList[0].startswith("{"): # DynamicSelect
    args = getStrings(removeFirstLastCurlBrackets(shapeList[0]))
    graphicsObject["visible"] = "true" in args[0]
  else:
    graphicsObject["visible"] = "true" in shapeList[0]
  # 2nd item is the origin
  originList = getStrings(removeFirstLastCurlBrackets(shapeList[1]))
  graphicsObject["origin"] = [float(originList[0]), float(originList[1])]
  # 3rd item is the rotation
  if shapeList[2].startswith("{"): # DynamicSelect
    args = getStrings(removeFirstLastCurlBrackets(shapeList[2]))
    graphicsObject["rotation"] = float(args[0])
  else:
    graphicsObject["rotation"] = float(shapeList[2])

def parseFilledShape(graphicsObject, shapeList):
  """Parses the Filled shape annotation."""
  # 4th item of list contains the line color.
  colorList = getStrings(removeFirstLastCurlBrackets(shapeList[3]))
  graphicsObject["lineColor"] = [int(colorList[0]), int(colorList[1]), int(colorList[2])]
  # 5th item of list contains the fill color.
  fillColorList = getStrings(removeFirstLastCurlBrackets(shapeList[4]))
  graphicsObject["fillColor"] = [int(fillColorList[0]), int(fillColorList[1]), int(fillColorList[2])]
  # 6th item of list contains the Line Pattern.
  graphicsObject["linePattern"] = shapeList[5]
  graphicsObject["fillPattern"] = shapeList[6]
  graphicsObject["lineThickness"] = float(shapeList[7])

def isFloat(value):
  """Checks if the value is float."""
  try:
    float(value)
    return True
  except ValueError:
    return False

def nodeToFileName(nodeName):
  """The file-system dislikes directory separators, * etc."""
  return nodeName.replace("/","Division").replace("*","Multiplication").replace("<","x3C").replace(">","x3E")

def generateSVGDownloadLink(fileName, serverName):
  """Generate the download link for the svg."""
  return "http://{0}/api/download/?filePath={1}".format(serverName, fileName)
