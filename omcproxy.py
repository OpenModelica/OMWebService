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

log = logging.getLogger(__name__)
omc = OMCSessionZMQ()

def ask_omc(expression, parsed=True):
  log.debug('ask_omc: {0}  - parsed: {1}'.format(expression, parsed))

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

if not ask_omc('loadModel(Modelica)', True):
  log.critical('Failed to load Modelica standard library: %s' % omc.sendExpression('getErrorString()'))

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
