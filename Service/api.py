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
Api module using the Flask framework.
"""

import os
import logging
import flask
from flask import jsonify
from flask_restx import Resource, Api, reqparse
from Service import omc
from werkzeug.datastructures import FileStorage
from werkzeug.utils import secure_filename
import tempfile
import zipfile

log = logging.getLogger(__name__)

api = Api(version="1.0", title="OMWebService API", description="OMWebService API Documentation")

@api.errorhandler
def defaultErrorHandler(error):
  """Default error handler"""
  return {"message": str(error)}, getattr(error, "code", 500)

@api.route("/version")
class Version(Resource):
  """End point to get OpenModelica version"""

  def get(self):
    """Gets the OpenModelica version"""
    return jsonify({"version": omc.sendCommand("getVersion()")})

@api.route("/simulate")
class Simulate(Resource):
  """End point to simulate a model"""

  parser = reqparse.RequestParser()
  parser.add_argument("Model Name", location = "form", required = True, help = "Name of the model")
  parser.add_argument("Model Zip File", location = "files", type = FileStorage, required = True, help = "Model zip file")

  allowedExtensions = set(['zip'])

  @api.expect(parser)
  def post(self):
    """Simulate the model."""
    args = self.parser.parse_args()
    modelName = args["Model Name"]
    modelZipFile = args["Model Zip File"]

    simulationResultJson = dict()

    # clear everything in omc
    omc.sendCommand("clear()")
    if modelZipFile and self.allowedFile(modelZipFile.filename):
      # save the zip file
      modelZipFileName = secure_filename(modelZipFile.filename)
      uploadDirectory = tempfile.mkdtemp()
      modelZipFilePath = os.path.join(uploadDirectory, modelZipFileName)
      modelZipFile.save(modelZipFilePath)
      # unzip the file
      with zipfile.ZipFile(modelZipFilePath, 'r') as zip_ref:
        zip_ref.extractall(uploadDirectory)
      # change working directory
      omc.sendCommand("cd(\"{0}\")".format(uploadDirectory.replace('\\','/')))
      # load the model in OMC
      if omc.sendCommand("loadFile(\"{0}.mo\")".format(os.path.splitext(modelZipFileName)[0])):
        # simulate the model
        simulationResult = omc.sendCommand("simulate({0})".format(modelName))
        if simulationResult["resultFile"]:
          simulationResultJson["messages"] = simulationResult["messages"]
          simulationResultJson["resultFile"] = flask.url_for('api.download', fileName="{0}/{1}".format(os.path.basename(uploadDirectory), os.path.basename(simulationResult["resultFile"])), _external=True)
          return jsonify(simulationResultJson)

    # if we reach here then some error occurred
    simulationResultJson["messages"] = "Failed to simulate the model."
    simulationResultJson["resultFile"] = ""
    return jsonify(simulationResultJson)

  def allowedFile(self, fileName):
    return '.' in fileName and fileName.rsplit('.', 1)[1].lower() in self.allowedExtensions

@api.route("/download/", doc=False)
class Download(Resource):
  """End point to download the svg file."""
  parser = reqparse.RequestParser()
  parser.add_argument("fileName", location = "args", required = True, help = "Path to download SVG file")

  @api.expect(parser)
  @api.produces(["application/octet-stream"])
  def get(self):
    """Downloads the mat simulation result file."""
    args = self.parser.parse_args()
    fileName = args["fileName"]
    return flask.send_file(tempfile.gettempdir() + "/" + fileName)