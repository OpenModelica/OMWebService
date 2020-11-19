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
util.py tests
"""

from OMWebService import util

def test_pythonBoolToModelicaBool():
  assert util.pythonBoolToModelicaBool(True) == "true"
  assert util.pythonBoolToModelicaBool(False) == "false"

def test_wordsBeforeAfterLastDot():
  assert util.wordsBeforeAfterLastDot("Modelica.Electrical", True) == "Electrical"
  assert util.wordsBeforeAfterLastDot("Modelica.Electrical", False) == "Modelica"
  assert util.wordsBeforeAfterLastDot("", True) == ""
  assert util.wordsBeforeAfterLastDot("", False) == ""
  assert util.wordsBeforeAfterLastDot(None, True) == ""
  assert util.wordsBeforeAfterLastDot(None, False) == ""

def test_getLastWordAfterDot():
  assert util.getLastWordAfterDot("Modelica.Electrical") == "Electrical"

def test_removeFirstLastCurlBrackets():
  assert util.removeFirstLastCurlBrackets("") == ""
  assert util.removeFirstLastCurlBrackets("{}") == ""
  assert util.removeFirstLastCurlBrackets("{some text}") == "some text"

def test_removeFirstLastParentheses():
  assert util.removeFirstLastParentheses("") == ""
  assert util.removeFirstLastParentheses("()") == ""
  assert util.removeFirstLastParentheses("(some text)") == "some text"

def test_unparseArrays():
  lst = ["{\"a\"}", "{\"b\"}"]
  assert util.unparseArrays("{{\"a\"}, {\"b\"}}") == lst

  value = "{{\"Modelica.Electrical.Analog.Interfaces.Pin\",\"p\",\"\", \"public\", \"false\", \"false\", \"false\", \"false\", \"unspecified\", \"none\", \"unspecified\",\"{}\"}}"
  assert len(util.unparseArrays(value)) == 1

  value = "{{\"Modelica.SIunits.Resistance\",\"R\",\"Resistance at temperature T_ref\", \"public\", \"false\", \"false\", \"false\", \"false\", \"parameter\", \"none\", \"unspecified\",\"{}\"}"\
          ",{\"Modelica.SIunits.Temperature\",\"T_ref\",\"Reference temperature\", \"public\", \"false\", \"false\", \"false\", \"false\", \"parameter\", \"none\", \"unspecified\",\"{}\"}"\
          ",{\"Modelica.SIunits.LinearTemperatureCoefficient\",\"alpha\",\"Temperature coefficient of resistance (R_actual = R*(1 + alpha*(T_heatPort - T_ref))\", \"public\", \"false\", \"false\", \"false\", \"false\", \"parameter\", \"none\", \"unspecified\",\"{}\"}"\
          ",{\"Modelica.SIunits.Resistance\",\"R_actual\",\"Actual resistance = R*(1 + alpha*(T_heatPort - T_ref))\", \"public\", \"false\", \"false\", \"false\", \"false\", \"unspecified\", \"none\", \"unspecified\",\"{}\"}}"
  assert len(util.unparseArrays(value)) == 4

def test_unparseStrings():
  lst = ["x", "y", "z"]
  assert util.unparseStrings("{\"x\", \"y\", \"z\"}") == lst

  value = "{\"Modelica.Electrical.Analog.Interfaces.Pin\",\"p\",\"\", \"public\", \"false\", \"false\", \"false\", \"false\", \"unspecified\", \"none\", \"unspecified\",\"{}\"}"
  assert len(util.unparseStrings(value)) == 12

def test_getStrings():
  value = "-100.0,-100.0,100.0,100.0,true,0.1,2.0,2.0, {Rectangle(true, {0.0, 0.0}, 0.0, {0, 0, 0}, {0, 0, 0}, LinePattern.Solid, FillPattern.None, 0.25, BorderPattern.None, {{-100.0, 100.0}, {100.0, -100.0}}, 0.0)}"
  lst = ["-100.0", "-100.0", "100.0", "100.0", "true", "0.1", "2.0", "2.0", "{Rectangle(true, {0.0, 0.0}, 0.0, {0, 0, 0}, {0, 0, 0}, LinePattern.Solid, FillPattern.None, 0.25, BorderPattern.None, {{-100.0, 100.0}, {100.0, -100.0}}, 0.0)}"]
  assert util.getStrings(value) == lst

def test_isFloat():
  assert util.isFloat(1.0) == True
  assert util.isFloat(2.3) == True
  assert util.isFloat(5) == True
  assert util.isFloat("5") == True
  assert util.isFloat("abc") == False

def test_nodeToFileName():
  assert util.nodeToFileName("abc/") == "abcDivision"
  assert util.nodeToFileName("abc*") == "abcMultiplication"
  assert util.nodeToFileName("abc/xyz*") == "abcDivisionxyzMultiplication"
  assert util.nodeToFileName("abc<xyz") == "abcx3Cxyz"
  assert util.nodeToFileName("abc>xyz") == "abcx3Exyz"
  assert util.nodeToFileName("abcxyz") == "abcxyz"
