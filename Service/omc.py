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

import logging
from OMPython import OMCSessionZMQ

log = logging.getLogger(__name__)

class OMC:
  """OpenModelica Compiler interface"""

  def __init__(self):
    self.omcSession = OMCSessionZMQ()
    self.errorString = ""

  def __del__(self):
    pass

  def sendCommand(self, expression, parsed=True):
    """Sends the command to OMC."""
    log.debug("OMC sendCommand: {0} - parsed: {1}".format(expression, parsed))

    try:
      res = self.omcSession.sendExpression(expression, parsed)
      log.debug("OMC result: {0}".format(res))
      if expression != "quit()":
        errorString = self.omcSession.sendExpression("getErrorString()")
        log.debug("OMC getErrorString(): {0}".format(errorString))
    except Exception as ex:
      log.error("OMC failed: {0}, parsed={1} with exception: {2}".format(expression, parsed, str(ex)))
      raise

    return res