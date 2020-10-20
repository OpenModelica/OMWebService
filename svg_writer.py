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
import math
import svgwrite
import os

log = logging.getLogger(__name__)

def getGradientColors(startColor, stopColor, mid_points):
  result = []

  startRed = int(startColor[0])
  startGreen = int(startColor[1])
  startBlue = int(startColor[2])

  stopRed = int(stopColor[0])
  stopGreen = int(stopColor[1])
  stopBlue = int(stopColor[2])

  r_delta = (stopRed - startRed) / (mid_points + 1)
  g_delta = (stopGreen - startGreen) / (mid_points + 1)
  b_delta = (stopBlue - startBlue) / (mid_points + 1)

  result.append((startRed, startGreen, startBlue))

  for i in range(1, mid_points + 1):
    result.append((startRed + i * r_delta, startGreen + i * g_delta, startBlue + i * b_delta))

  result.append((stopRed, stopGreen, stopBlue))

  return result

def getCoordinates(xy, graphics, minX, maxY, transformation, coordinateSystem):
  x = xy[0] + graphics['origin'][0]
  y = xy[1] + graphics['origin'][1]

  # rotation for the icon
  s = math.sin(graphics['rotation'] / 180 * 3.1415)
  c = math.cos(graphics['rotation'] / 180 * 3.1415)

  x -= graphics['origin'][0]
  y -= graphics['origin'][1]

  xnew = x * c - y * s
  ynew = x * s + y * c

  x = xnew + graphics['origin'][0]
  y = ynew + graphics['origin'][1]

  if transformation and coordinateSystem:
    try:
      t_width = abs(max(transformation['extent'][1][0], transformation['extent'][0][0]) - min(transformation['extent'][1][0], transformation['extent'][0][0]))
      t_height = abs(max(transformation['extent'][1][1], transformation['extent'][0][1]) - min(transformation['extent'][1][1], transformation['extent'][0][1]))
      o_width = abs(max(coordinateSystem['extent'][1][0], coordinateSystem['extent'][0][0]) - min(coordinateSystem['extent'][1][1], coordinateSystem['extent'][0][1]))
      o_height = abs(max(coordinateSystem['extent'][1][1], coordinateSystem['extent'][0][1]) - min(coordinateSystem['extent'][1][1], coordinateSystem['extent'][0][1]))

      if 'extent' in transformation and transformation['extent'][1][0] < transformation['extent'][0][0]:
        # horizontal flip
        x = (-xy[0] + graphics['origin'][0]) / o_width * t_width + transformation['origin'][0] + transformation['extent'][1][0] + t_width / 2
      else:
        x = (xy[0] + graphics['origin'][0]) / o_width * t_width + transformation['origin'][0] + transformation['extent'][0][0] + t_width / 2

      if 'extent' in transformation and transformation['extent'][1][1] < transformation['extent'][0][1]:
        # vertical flip
        y = (-xy[1] + graphics['origin'][1]) / o_height * t_height + transformation['origin'][1] + min(transformation['extent'][1][1], transformation['extent'][0][1]) + t_height / 2
      else:
        y = (xy[1] + graphics['origin'][1]) / o_height * t_height + transformation['origin'][1] + min(transformation['extent'][0][1], transformation['extent'][0][1]) + t_height / 2

      s = math.sin(transformation['rotation'] / 180 * 3.1415)
      c = math.cos(transformation['rotation'] / 180 * 3.1415)

      x -= transformation['origin'][0]
      y -= transformation['origin'][1]

      xnew = x * c - y * s
      ynew = x * s + y * c

      x = xnew + transformation['origin'][0]
      y = ynew + transformation['origin'][1]

    except KeyError as ex:
      log.error("Component position transformation failed: {0}".format(ex.message))
      log.error(graphics)

  x -= minX
  y = maxY - y

  return x, y

def getShapeSvgFromGraphics(dwg, graphics, minX, maxY, elementId, transformation=None, coordinateSystem=None):
  shape = None
  definitions = svgwrite.container.Defs()
  origin = None

  if not 'origin' in graphics:
    graphics['origin'] = (0, 0)

  origin = graphics['origin']

  if graphics['type'] == 'Rectangle' or graphics['type'] == 'Ellipse' or graphics['type'] == 'Text' or graphics['type'] == "Bitmap":
    (x0, y0) = getCoordinates(graphics['extent'][0], graphics, minX, maxY, transformation, coordinateSystem)
    (x1, y1) = getCoordinates(graphics['extent'][1], graphics, minX, maxY, transformation, coordinateSystem)

  if graphics['type'] == 'Rectangle' or graphics['type'] == 'Ellipse' or graphics['type'] == 'Polygon':
    if not 'fillPattern' in graphics:
      graphics['fillPattern'] = 'FillPattern.None'

  if graphics['type'] == 'Rectangle':
    shape = dwg.rect((min(x0, x1), min(y0, y1)), (abs(x1 - x0), abs(y1 - y0)), graphics['radius'], graphics['radius'])

  elif graphics['type'] == 'Line':
    if 'points' in graphics:
      if graphics['smooth'] == 'Smooth.Bezier' and len(graphics['points']) > 2:
        # TODO: Optimize this part!!!
        shape = svgwrite.path.Path()
        x_0, y_0 = getCoordinates([graphics['points'][0][0], graphics['points'][0][1]], graphics, minX, maxY, transformation, coordinateSystem)
        shape.push('M', x_0, y_0, 'C')

        for i in range(1, len(graphics['points']) - 1):
          x_0, y_0 = getCoordinates([graphics['points'][i-1][0], graphics['points'][i-1][1]], graphics, minX, maxY, transformation, coordinateSystem)
          x_1, y_1 = getCoordinates([graphics['points'][i][0], graphics['points'][i][1]], graphics, minX, maxY, transformation, coordinateSystem)
          x_2, y_2 = getCoordinates([graphics['points'][i+1][0], graphics['points'][i+1][1]], graphics, minX, maxY, transformation, coordinateSystem)
          x_01 = (x_1 + x_0) / 2
          y_01 = (y_1 + y_0) / 2
          x_12 = (x_2 + x_1) / 2
          y_12 = (y_2 + y_1) / 2
          shape.push(x_01, y_01, x_1, y_1, x_12, y_12)
        x_n, y_n = getCoordinates([graphics['points'][len(graphics['points']) - 1][0], graphics['points'][len(graphics['points']) - 1][1]], graphics, minX, maxY, transformation, coordinateSystem)
        shape.push(x_12, y_12, x_n, y_n, x_n, y_n)
      else:
        shape = dwg.polyline([getCoordinates([x, y], graphics, minX, maxY, transformation, coordinateSystem) for (x, y) in graphics['points']])
      shape.fill('none', opacity=0)

      # markers
      if graphics['arrow'][0] != 'Arrow.None':
        url_id_start = graphics['arrow'][0] + '_start' + str(elementId)
        elementId += 1
        marker = svgwrite.container.Marker(insert=(10, 5), size=(4, 3), orient='auto', id=url_id_start, viewBox="0 0 10 10")
        p = svgwrite.path.Path(d="M 10 0 L 0 5 L 10 10 z")
        p.fill("rgb(" + ','.join([str(v) for v in graphics['color']]) + ")")
        marker.add(p)
        definitions.add(marker)
        shape['marker-start'] = marker.get_funciri()

      if graphics['arrow'][1] != 'Arrow.None':
        url_id_end = graphics['arrow'][1] + '_end' + str(elementId)
        elementId += 1
        marker = svgwrite.container.Marker(insert=(0, 5), size=(4, 3), orient='auto', id=url_id_end, viewBox="0 0 10 10")
        p = svgwrite.path.Path(d="M 0 0 L 10 5 L 0 10 z")
        p.fill("rgb(" + ','.join([str(v) for v in graphics['color']]) + ")")
        marker.add(p)
        definitions.add(marker)
        shape['marker-end'] = marker.get_funciri()

    else:
      log.error('Not handled: {0}'.format(graphics))
      return None

  elif graphics['type'] == 'Polygon':
    if 'points' in graphics:
      if graphics['smooth'] == 'Smooth.Bezier' and len(graphics['points']) > 2:
        # TODO: Optimize this part!!!
        shape = svgwrite.path.Path()
        x_0, y_0 = getCoordinates([graphics['points'][0][0], graphics['points'][0][1]], graphics, minX, maxY, transformation, coordinateSystem)
        shape.push('M', x_0, y_0, 'C')

        for i in range(1, len(graphics['points']) - 1):
          x_0, y_0 = getCoordinates([graphics['points'][i-1][0], graphics['points'][i-1][1]], graphics, minX, maxY, transformation, coordinateSystem)
          x_1, y_1 = getCoordinates([graphics['points'][i][0], graphics['points'][i][1]], graphics, minX, maxY, transformation, coordinateSystem)
          x_2, y_2 = getCoordinates([graphics['points'][i+1][0], graphics['points'][i+1][1]], graphics, minX, maxY, transformation, coordinateSystem)
          x_01 = (x_1 + x_0) / 2
          y_01 = (y_1 + y_0) / 2
          x_12 = (x_2 + x_1) / 2
          y_12 = (y_2 + y_1) / 2
          shape.push(x_01, y_01, x_1, y_1, x_12, y_12)
        x_n, y_n = getCoordinates([graphics['points'][len(graphics['points']) - 1][0], graphics['points'][len(graphics['points']) - 1][1]], graphics, minX, maxY, transformation, coordinateSystem)
        shape.push(x_12, y_12, x_n, y_n, x_n, y_n)
      else:
        shape = dwg.polygon([getCoordinates([x, y], graphics, minX, maxY, transformation, coordinateSystem) for (x, y) in graphics['points']])
      shape.fill('none', opacity=0)
    else:
      log.error('Not handled: {0}'.format(graphics))
      return None

  elif graphics['type'] == 'Ellipse':
    shape = dwg.ellipse(((x0 + x1) / 2, (y0 + y1) / 2), (abs((x1 - x0) / 2), abs((y1 - y0) / 2)))

  elif graphics['type'] == 'Text':
    extra = {}
    x = (x0 + x1) / 2
    y = (y0 + y1) / 2

    extra['font_family'] = graphics['fontName'] or "Verdana"

    if graphics['fontSize'] == 0:
      extra['font_size'] = str(abs(y1-y0)) # fit text into extent according to 18.6.5.5
    else:
      extra['font_size'] = graphics['fontSize']

    for style in graphics['textStyle']:
      if style == "TextStyle.Bold":
        extra['font-weight'] = 'bold'
      elif style == "TextStyle.Italic":
        extra['font-style'] = 'italic'
      elif style == "TextStyle.UnderLine":
        extra['text-decoration'] = 'underline'

    extra['dominant_baseline'] = "middle"

    if graphics['horizontalAlignment'] == "TextAlignment.Left":
      extra['text_anchor'] = "start"
      if x0 < x1:
        x = x0
      else:
        x = x1
      if y0 < y1:
        y = y0
      else:
        y = y1
    elif graphics['horizontalAlignment'] == "TextAlignment.Center":
      extra['text_anchor'] = "middle"
    elif graphics['horizontalAlignment'] == "TextAlignment.Right":
      extra['text_anchor'] = "end"
      if x0 < x1:
        x = x1
      else:
        x = x0
      if y0 < y1:
        y = y1
      else:
        y = y0

    shape = dwg.text(graphics['textString'], None, [x], [y], **extra)

  elif graphics['type'] == 'Bitmap':
    xmin = x0
    ymin = y0
    xmax = x1
    ymax = y1

    if x0 > x1:
      xmin = x1
      xmax = x0
    if y0 > y1:
      ymin = y1
      ymax = y0
    shape = dwg.image(graphics['href'], x=xmin,y=ymin,width=xmax-xmin,height=ymax-ymin) # put in correct URL or base64 data "data:image;base64,"

  elif graphics['type'] == 'Empty':
    return None

  else:
    log.warning('Not handled: {0}'.format(graphics))
    return None

  dot_size = 4
  dash_size = 16
  space_size = 8

  if 'linePattern' in graphics:
    dot_size *= graphics['lineThickness']
    dash_size *= graphics['lineThickness']
    space_size *= graphics['lineThickness']

    if graphics['linePattern'] == 'LinePattern.None' or graphics['type'] == 'Text':
      pass
    elif graphics['linePattern'] == 'LinePattern.Solid':
      shape.stroke("rgb(" + ','.join([str(v) for v in graphics['lineColor']]) + ")", width='{0}mm'.format(graphics['lineThickness']))
    elif graphics['linePattern'] == 'LinePattern.Dash':
      shape.stroke("rgb(" + ','.join([str(v) for v in graphics['lineColor']]) + ")", width='{0}mm'.format(graphics['lineThickness']))
      shape.dasharray([dash_size, space_size])
    elif graphics['linePattern'] == 'LinePattern.Dot':
      shape.stroke("rgb(" + ','.join([str(v) for v in graphics['lineColor']]) + ")", width='{0}mm'.format(graphics['lineThickness']))
      shape.dasharray([dot_size, space_size])
    elif graphics['linePattern'] == 'LinePattern.DashDot':
      shape.stroke("rgb(" + ','.join([str(v) for v in graphics['lineColor']]) + ")", width='{0}mm'.format(graphics['lineThickness']))
      shape.dasharray([dash_size, space_size, dot_size, space_size])
    elif graphics['linePattern'] == 'LinePattern.DashDotDot':
      shape.stroke("rgb(" + ','.join([str(v) for v in graphics['lineColor']]) + ")", width='{0}mm'.format(graphics['lineThickness']))
      shape.dasharray([dash_size, space_size, dot_size, space_size, dot_size, space_size])

    if graphics['type'] == 'Rectangle':
      if graphics['borderPattern'] == 'BorderPattern.None':
        pass
      elif graphics['borderPattern'] == 'BorderPattern.Raised':
        url_id = graphics['borderPattern'] + '_' + str(elementId)
        elementId += 1
        shape['filter'] = 'url(#' + url_id + ')'

        filter = svgwrite.filters.Filter(id=url_id, filterUnits="objectBoundingBox", x="-0.1", y="-0.1", width="1.2", height="1.2")
        filter.feGaussianBlur("SourceAlpha", stdDeviation="5", result="alpha_blur")
        feSL = filter.feSpecularLighting("alpha_blur", surfaceScale="5", specularConstant="1", specularExponent="20", lighting_color="#FFFFFF", result="spec_light")
        feSL.fePointLight((-5000, -10000, 10000))
        filter.feComposite("spec_light", in2="SourceAlpha", operator="in", result="spec_light")
        filter.feComposite("SourceGraphic", in2="spec_light", operator="out", result="spec_light_fill")

        definitions.add(filter)
      elif graphics['borderPattern'] == 'BorderPattern.Sunken':
        log.warning('Not supported: {0}'.format(graphics['borderPattern']))
      elif graphics['borderPattern'] == 'BorderPattern.Engraved':
        log.warning('Not supported: {0}'.format(graphics['borderPattern']))

  if 'color' in graphics:
    try:
      shape.stroke("rgb(" + ','.join([str(v) for v in graphics['color']]) + ")", width='{0}mm'.format(graphics['thickness']))
    except TypeError as ex:
      log.error('{0} {1}'.format(graphics['color'], ex.message))

  if 'pattern' in graphics:
    dot_size *= graphics['thickness']
    dash_size *= graphics['thickness']
    space_size *= graphics['thickness']

    if graphics['pattern'] == 'LinePattern.None' or graphics['type'] == 'Text':
      pass
    elif graphics['pattern'] == 'LinePattern.Solid':
      shape.stroke("rgb(" + ','.join([str(v) for v in graphics['color']]) + ")", width='{0}mm'.format(graphics['thickness']))
    elif graphics['pattern'] == 'LinePattern.Dash':
      shape.stroke("rgb(" + ','.join([str(v) for v in graphics['color']]) + ")", width='{0}mm'.format(graphics['thickness']))
      shape.dasharray([dash_size, space_size])
    elif graphics['pattern'] == 'LinePattern.Dot':
      shape.stroke("rgb(" + ','.join([str(v) for v in graphics['color']]) + ")", width='{0}mm'.format(graphics['thickness']))
      shape.dasharray([dot_size, space_size])
    elif graphics['pattern'] == 'LinePattern.DashDot':
      shape.stroke("rgb(" + ','.join([str(v) for v in graphics['color']]) + ")", width='{0}mm'.format(graphics['thickness']))
      shape.dasharray([dash_size, space_size, dot_size, space_size])
    elif graphics['pattern'] == 'LinePattern.DashDotDot':
      shape.stroke("rgb(" + ','.join([str(v) for v in graphics['color']]) + ")", width='{0}mm'.format(graphics['thickness']))
      shape.dasharray([dash_size, space_size, dot_size, space_size, dot_size, space_size])

  if 'fillPattern' in graphics:
    if graphics['fillPattern'] == 'FillPattern.None':
      if graphics['type'] == 'Text':
        shape.fill("rgb(" + ','.join([str(v) for v in graphics['lineColor']]) + ")", opacity=1)
      else:
        shape.fill('none', opacity=0)
    elif graphics['fillPattern'] == 'FillPattern.Solid':
      shape.fill("rgb(" + ','.join([str(v) for v in graphics['fillColor']]) + ")", opacity=1)
    elif graphics['fillPattern'] == 'FillPattern.Horizontal':
      url_id = str(elementId)
      elementId += 1
      shape.fill('url(#' + url_id + ')')

      pattern = svgwrite.pattern.Pattern(id=url_id, insert=(0, 0), size=(5, 5), patternUnits='userSpaceOnUse')

      rect = svgwrite.shapes.Rect(insert=(0, 0), size=(5, 5))
      rect.fill("rgb(" + ','.join([str(v) for v in graphics['fillColor']]) + ")")
      pattern.add(rect)

      svg_path = svgwrite.path.Path(d="M0,0 L5,0")
      svg_path.stroke("rgb(" + ','.join([str(v) for v in graphics['lineColor']]) + ")", width=2)
      pattern.add(svg_path)

      definitions.add(pattern)

    elif graphics['fillPattern'] == 'FillPattern.Vertical':
      url_id = str(elementId)
      elementId += 1
      shape.fill('url(#' + url_id + ')')

      pattern = svgwrite.pattern.Pattern(id=url_id, insert=(0, 0), size=(5, 5), patternUnits='userSpaceOnUse')

      rect = svgwrite.shapes.Rect(insert=(0, 0), size=(5, 5))
      rect.fill("rgb(" + ','.join([str(v) for v in graphics['fillColor']]) + ")")
      pattern.add(rect)

      svg_path = svgwrite.path.Path(d="M0,0 L0,5")
      svg_path.stroke("rgb(" + ','.join([str(v) for v in graphics['lineColor']]) + ")", width=2)
      pattern.add(svg_path)

      definitions.add(pattern)

    elif graphics['fillPattern'] == 'FillPattern.Cross':
      url_id = str(elementId)
      elementId += 1
      shape.fill('url(#' + url_id + ')')

      pattern = svgwrite.pattern.Pattern(id=url_id, insert=(0, 0), size=(5, 5), patternUnits='userSpaceOnUse')

      rect = svgwrite.shapes.Rect(insert=(0, 0), size=(5, 5))
      rect.fill("rgb(" + ','.join([str(v) for v in graphics['fillColor']]) + ")")
      pattern.add(rect)

      svg_path = svgwrite.path.Path(d="M0,0 L5,0")
      svg_path.stroke("rgb(" + ','.join([str(v) for v in graphics['lineColor']]) + ")", width=2)
      pattern.add(svg_path)

      svg_path = svgwrite.path.Path(d="M0,0 L0,5")
      svg_path.stroke("rgb(" + ','.join([str(v) for v in graphics['lineColor']]) + ")", width=2)
      pattern.add(svg_path)

      definitions.add(pattern)

    elif graphics['fillPattern'] == 'FillPattern.Forward':
      url_id = str(elementId)
      elementId += 1
      shape.fill('url(#' + url_id + ')')

      pattern = svgwrite.pattern.Pattern(id=url_id, insert=(0, 0), size=(7, 7), patternUnits='userSpaceOnUse')

      rect = svgwrite.shapes.Rect(insert=(0, 0), size=(7, 7))
      rect.fill("rgb(" + ','.join([str(v) for v in graphics['fillColor']]) + ")")
      pattern.add(rect)

      svg_path = svgwrite.path.Path(d="M0,0 l7,7")
      svg_path.stroke("rgb(" + ','.join([str(v) for v in graphics['lineColor']]) + ")", width=1)
      pattern.add(svg_path)

      svg_path = svgwrite.path.Path(d="M6,-1 l3,3")
      svg_path.stroke("rgb(" + ','.join([str(v) for v in graphics['lineColor']]) + ")", width=1)
      pattern.add(svg_path)

      svg_path = svgwrite.path.Path(d="M-1,6 l3,3")
      svg_path.stroke("rgb(" + ','.join([str(v) for v in graphics['lineColor']]) + ")", width=1)
      pattern.add(svg_path)

      definitions.add(pattern)

    elif graphics['fillPattern'] == 'FillPattern.Backward':
      url_id = str(elementId)
      elementId += 1
      shape.fill('url(#' + url_id + ')')

      pattern = svgwrite.pattern.Pattern(id=url_id, insert=(0, 0), size=(7, 7), patternUnits='userSpaceOnUse')

      rect = svgwrite.shapes.Rect(insert=(0, 0), size=(7, 7))
      rect.fill("rgb(" + ','.join([str(v) for v in graphics['fillColor']]) + ")")
      pattern.add(rect)

      svg_path = svgwrite.path.Path(d="M7,0 l-7,7")
      svg_path.stroke("rgb(" + ','.join([str(v) for v in graphics['lineColor']]) + ")", width=1)
      pattern.add(svg_path)

      svg_path = svgwrite.path.Path(d="M1,-1 l-7,7")
      svg_path.stroke("rgb(" + ','.join([str(v) for v in graphics['lineColor']]) + ")", width=1)
      pattern.add(svg_path)

      svg_path = svgwrite.path.Path(d="M8,6 l-7,7")
      svg_path.stroke("rgb(" + ','.join([str(v) for v in graphics['lineColor']]) + ")", width=1)
      pattern.add(svg_path)

      definitions.add(pattern)

    elif graphics['fillPattern'] == 'FillPattern.CrossDiag':

      url_id = str(elementId)
      elementId += 1
      shape.fill('url(#' + url_id + ')')

      pattern = svgwrite.pattern.Pattern(id=url_id, insert=(0, 0), size=(8, 8), patternUnits='userSpaceOnUse')

      rect = svgwrite.shapes.Rect(insert=(0, 0), size=(8, 8))
      rect.fill("rgb(" + ','.join([str(v) for v in graphics['fillColor']]) + ")")
      pattern.add(rect)

      svg_path = svgwrite.path.Path(d="M0,0 l8,8")
      svg_path.stroke("rgb(" + ','.join([str(v) for v in graphics['lineColor']]) + ")", width=1)
      pattern.add(svg_path)

      svg_path = svgwrite.path.Path(d="M8,0 l-8,8")
      svg_path.stroke("rgb(" + ','.join([str(v) for v in graphics['lineColor']]) + ")", width=1)
      pattern.add(svg_path)

      definitions.add(pattern)

    elif graphics['fillPattern'] == 'FillPattern.HorizontalCylinder':

      url_id = str(elementId)
      elementId += 1
      shape.fill('url(#' + url_id + ')')

      lineColor = graphics['lineColor']
      fillColor = graphics['fillColor']

      if not lineColor:
        lineColor = 'black'
      if not fillColor:
        fillColor = 'white'

      gradient = svgwrite.gradients.LinearGradient(id=url_id, x1="0%", y1="0%", x2="0%", y2="100%")

      colors = getGradientColors(lineColor, fillColor, 0)

      stopValues = [
        (0, 0),
        (0.3, 1),
        (0.7, 1),
        (1, 0)
      ]

      for (stopValue, idx) in stopValues:
        gradient.add_stop_color(offset=stopValue, color='rgb({0}, {1}, {2})'.format(colors[idx][0], colors[idx][1], colors[idx][2]), opacity=1)

      definitions.add(gradient)

    elif graphics['fillPattern'] == 'FillPattern.VerticalCylinder':
      url_id = str(elementId)
      elementId += 1
      shape.fill('url(#' + url_id + ')')

      lineColor = graphics['lineColor']
      fillColor = graphics['fillColor']

      if not lineColor:
        lineColor = 'black'
      if not fillColor:
        fillColor = 'white'

      gradient = svgwrite.gradients.LinearGradient(id=url_id, x1="0%", y1="0%", x2="100%", y2="0%")

      colors = getGradientColors(lineColor, fillColor, 0)

      stopValues = [
        (0, 0),
        (0.3, 1),
        (0.7, 1),
        (1, 0)
      ]

      for (stopValue, idx) in stopValues:
        gradient.add_stop_color(offset=stopValue, color='rgb({0}, {1}, {2})'.format(colors[idx][0], colors[idx][1], colors[idx][2]), opacity=1)

      definitions.add(gradient)
    elif graphics['fillPattern'] == 'FillPattern.Sphere':
      if graphics['type'] == 'Ellipse':
        url_id = str(elementId)
        elementId += 1

        shape.fill('url(#' + url_id + ')')

        lineColor = graphics['lineColor']
        fillColor = graphics['fillColor']

        if not lineColor:
          lineColor = 'black'
        if not fillColor:
          fillColor = 'white'

        gradient = svgwrite.gradients.RadialGradient(id=url_id, cx="50%", cy="50%", r="55%", fx="50%", fy="50%")
        colors = getGradientColors(lineColor, fillColor, 9)

        stopValues = [
          (0, 10),
          (0.45, 8),
          (0.7, 6),
          (1, 0)
        ]

        for (stopValue, idx) in stopValues:
          gradient.add_stop_color(offset=stopValue, color='rgb({0}, {1}, {2})'.format(int(colors[idx][0]), int(colors[idx][1]), int(colors[idx][2])), opacity=1)

        definitions.add(gradient)
      elif graphics['type'] == 'Rectangle':
        url_id = str(elementId)
        elementId += 1

        shape.fill('url(#' + url_id + ')')

        lineColor = graphics['lineColor']
        fillColor = graphics['fillColor']

        if not lineColor:
          lineColor = 'black'
        if not fillColor:
          fillColor = 'white'

        gradient = svgwrite.gradients.RadialGradient(id=url_id, cx="50%", cy="50%", r="0.9", fx="50%", fy="50%")

        colors = getGradientColors(lineColor, fillColor, 0)

        stopValues = [
          (0, 1),
          (1, 0)
        ]

        for (stopValue, idx) in stopValues:
          gradient.add_stop_color(offset=stopValue, color='rgb({0}, {1}, {2})'.format(colors[idx][0], colors[idx][1], colors[idx][2]), opacity=1)

        definitions.add(gradient)
  else:
      if graphics['type'] != 'Bitmap':
        shape.fill('none', opacity=0)
  return shape, definitions

def writeSVG(fileName, iconGraphics):
  elementId = 0
  width = 100
  height = 100

  minX = 0
  minY = 0
  maxX = 100
  maxY = 100

  for iconGraphic in iconGraphics:
    for graphics in iconGraphic['graphics']:
      
      if not 'origin' in graphics:
        graphics['origin'] = (0, 0)

      if not 'extent' in graphics:
        graphics['extent'] = [[-100, -100], [100, 100]]

      if 'extent' in graphics:
        minX = min(minX, graphics['extent'][0][0] + graphics['origin'][0])
        minX = min(minX, graphics['extent'][1][0] + graphics['origin'][0])
        minY = min(minY, graphics['extent'][0][1] + graphics['origin'][1])
        minY = min(minY, graphics['extent'][1][1] + graphics['origin'][1])
        maxX = max(maxX, graphics['extent'][1][0] + graphics['origin'][0])
        maxX = max(maxX, graphics['extent'][0][0] + graphics['origin'][0])
        maxY = max(maxY, graphics['extent'][1][1] + graphics['origin'][1])
        maxY = max(maxY, graphics['extent'][0][1] + graphics['origin'][1])

      if 'points' in graphics:
        for point in graphics['points']:
          minX = min(minX, point[0] + graphics['origin'][0])
          minY = min(minY, point[1] + graphics['origin'][1])
          maxX = max(maxX, point[0] + graphics['origin'][0])
          maxX = max(maxY, point[1] + graphics['origin'][1])

  width = maxX - minX
  height = maxY - minY

  dwg = svgwrite.Drawing(fileName, size=(width, height), viewBox="0 0 " + str(width) + " " + str(height))
  # Makes hashing not work
  # dwg.add(svgwrite.base.Desc(iconGraphics[-1]['className']))

  for iconGraphic in iconGraphics:
    for graphics in iconGraphic['graphics']:
      svgShape = getShapeSvgFromGraphics(dwg, graphics, minX, maxY, elementId)
      if svgShape:
        dwg.add(svgShape[0])
        dwg.add(svgShape[1])

  dwg.save(pretty=True)
  return width, height


