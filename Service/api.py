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
import string
import flask
from flask import current_app, jsonify
from flask_restx import Resource, Api, reqparse
from Service.omc import OMC
from Service import util
from werkzeug.datastructures import FileStorage
from werkzeug.utils import secure_filename
import tempfile
import zipfile
import json

log = logging.getLogger(__name__)

api = Api(version="1.0", title="OMWebService API", description="OMWebService API Documentation")

allowedExtensions = set(["zip", "json"])

def allowedFile(fileName):
  return '.' in fileName and fileName.rsplit('.', 1)[1].lower() in allowedExtensions

def setResultJsonAndQuitOMC(omc, originalDir, messages, file):
  resultJson = dict()
  if originalDir:
    omc.sendCommand("cd(\"{0}\")".format(originalDir.replace('\\','/')))
  omc.sendCommand("quit()")
  resultJson["messages"] = messages
  resultJson["file"] = file
  return jsonify(resultJson)

def readMetaDataAndZipFile(omc, metaDataJsonFileArg, modelZipFileArg):
  uploadDirectory = ""
  metaDataJson = {}
  # save and read the json file
  if metaDataJsonFileArg and allowedFile(metaDataJsonFileArg.filename):
    metaDataJsonFileName = secure_filename(metaDataJsonFileArg.filename)
    uploadDirectory = tempfile.mkdtemp(dir=current_app.config['TMPDIR'])
    # change working directory
    omc.sendCommand("cd(\"{0}\")".format(uploadDirectory.replace('\\','/')))
    metaDataJsonFilePath = os.path.join(uploadDirectory, metaDataJsonFileName)
    metaDataJsonFileArg.save(metaDataJsonFilePath)
    try:
      with open(metaDataJsonFilePath) as metaDataJsonFile:
        metaDataJson = json.load(metaDataJsonFile)
    # json file not found exception
    except FileNotFoundError:
      return False, uploadDirectory, "The metadata.json file is missing. {0}".format(metaDataJsonFilePath), metaDataJson
  else:
    return False, uploadDirectory, "The metadata.json file is missing. {0}".format(metaDataJsonFilePath), metaDataJson

  # save and read the zip file
  if modelZipFileArg and allowedFile(modelZipFileArg.filename):
    modelZipFileName = secure_filename(modelZipFileArg.filename)
    modelZipFilePath = os.path.join(uploadDirectory, modelZipFileName)
    modelZipFileArg.save(modelZipFilePath)
    # unzip the file
    with zipfile.ZipFile(modelZipFilePath, 'r') as zip_ref:
      zip_ref.extractall(uploadDirectory)

  # load the model in OMC
  fileNames = metaDataJson.get("fileNames", [])
  for fileName in fileNames:
    if not omc.sendCommand("loadFile(\"{0}\")".format(fileName)):
      return False, uploadDirectory, "Failed to load the model file {0}. {1}".format(fileName, omc.errorString), metaDataJson

  # load the libs
  libs = metaDataJson.get("libs", [])
  for lib in libs:
    name = lib.get("name", "")
    version = lib.get("version", "")
    if not omc.sendCommand("installPackage({0}, \"{1}\")".format(name, version)):
      return False, uploadDirectory, "Failed to install package {0}.".format(name), metaDataJson
    if not omc.sendCommand("loadModel({0}, {{\"{1}\"}})".format(name, version)):
      return False, uploadDirectory, "Failed to load package {0}.".format(name), metaDataJson

  return True, uploadDirectory, "", metaDataJson

@api.errorhandler
def defaultErrorHandler(error):
  """Default error handler"""
  return {"message": str(error)}, getattr(error, "code", 500)

@api.route("/version")
class Version(Resource):
  """End point to get OpenModelica version"""

  def get(self):
    """Gets the OpenModelica version"""
    omc = OMC()
    version = omc.sendCommand("getVersion()")
    omc.sendCommand("quit()")
    return jsonify({"version": version})

@api.route("/simulate")
class Simulate(Resource):
  """End point to simulate a model"""

  parser = reqparse.RequestParser()
  parser.add_argument("MetadataJson", location = "files", type = FileStorage, required = True, help = "JSON file with simulation data information")
  parser.add_argument("ModelZip", location = "files", type = FileStorage, help = "Zip file containing the extra Modelica files needed for simulation")

  @api.expect(parser)
  def post(self):
    """Simulate the model."""
    args = self.parser.parse_args()
    metaDataJsonFileArg = args["MetadataJson"]
    modelZipFileArg = args["ModelZip"]

    omc = OMC()
    originalDir = omc.sendCommand("cd()")
    metaDataJson = {}
    file = ""

    status, uploadDirectory, messages, metaDataJson = readMetaDataAndZipFile(omc, metaDataJsonFileArg, modelZipFileArg)
    if not status:
      return setResultJsonAndQuitOMC(omc, originalDir, messages, file)

    # simulate the model
    className = metaDataJson.get("class", "")
    if className:
      simulationArguments = []
      if "fileNamePrefix" in metaDataJson:
        simulationArguments.append("fileNamePrefix=\"{0}\"".format(metaDataJson["fileNamePrefix"]))

      outputFormat = metaDataJson.get("outputFormat", "mat")
      if outputFormat.casefold() == "fmu":
        if "fmuVersion" in metaDataJson:
          simulationArguments.append("version={0}".format(metaDataJson["fmuVersion"]))
        if "fmuType" in metaDataJson:
          simulationArguments.append("fmuType={0}".format(metaDataJson["fmuType"]))
        if "platforms" in metaDataJson:
          platforms = []
          platformsJson = metaDataJson.get("platforms", [])
          for platform in platformsJson:
            platforms.append("\"{0}\"".format(platform))
          simulationArguments.append("platforms={{{0}}}".format(", ".join(platforms)))
        if "includeResources" in metaDataJson:
          simulationArguments.append("includeResources={0}".format(metaDataJson["includeResources"]))
      else:
        if "startTime" in metaDataJson:
          simulationArguments.append("startTime={0}".format(metaDataJson["startTime"]))
        if "stopTime" in metaDataJson:
          simulationArguments.append("stopTime={0}".format(metaDataJson["stopTime"]))
        if "numberOfIntervals" in metaDataJson:
          simulationArguments.append("numberOfIntervals={0}".format(metaDataJson["numberOfIntervals"]))
        if "tolerance" in metaDataJson:
          simulationArguments.append("tolerance={0}".format(metaDataJson["tolerance"]))
        if "method" in metaDataJson:
          simulationArguments.append("method=\"{0}\"".format(metaDataJson["method"]))
        if "options" in metaDataJson:
          simulationArguments.append("options=\"{0}\"".format(metaDataJson["options"]))
        if outputFormat.casefold() == "mat" or outputFormat.casefold() == "csv":
          simulationArguments.append("outputFormat=\"{0}\"".format(outputFormat))
        if "variableFilter" in metaDataJson:
          simulationArguments.append("variableFilter=\"{0}\"".format(metaDataJson["variableFilter"]))
        if "cflags" in metaDataJson:
          simulationArguments.append("cflags=\"{0}\"".format(metaDataJson["cflags"]))
        if "simflags" in metaDataJson:
          simulationArguments.append("simflags=\"{0}\"".format(metaDataJson["simflags"]))

      simulationArgumentsStr = ", ".join(simulationArguments)
      if simulationArgumentsStr:
        simulationArgumentsStr = ", " + simulationArgumentsStr

      if outputFormat.casefold() == "fmu":
        simulationResult = omc.sendCommand("buildModelFMU({0}{1})".format(className, simulationArgumentsStr))
        if simulationResult:
          messages = "FMU is generated."
          file = flask.url_for('api.download', FileName="{0}/{1}".format(os.path.basename(uploadDirectory), os.path.basename(simulationResult)), _external=True)
        else:
          messages = "Failed to generate the FMU. {0}".format(omc.errorString)
          file = ""
      else:
        simulationResult = omc.sendCommand("simulate({0}{1})".format(className, simulationArgumentsStr))
        messages = simulationResult["messages"]
        if simulationResult["resultFile"]:
          file = flask.url_for('api.download', FileName="{0}/{1}".format(os.path.basename(uploadDirectory), os.path.basename(simulationResult["resultFile"])), _external=True)
        else:
          file = ""
    else:
      messages = "Class is missing."
      file = ""
    
    return setResultJsonAndQuitOMC(omc, originalDir, messages, file)

@api.route("/download/", doc=False)
class Download(Resource):
  """End point to download the svg file."""
  parser = reqparse.RequestParser()
  parser.add_argument("FileName", location = "args", required = True, help = "Path to download SVG file")

  @api.expect(parser)
  @api.produces(["application/octet-stream"])
  def get(self):
    """Downloads the mat simulation result file."""
    args = self.parser.parse_args()
    fileName = args["FileName"]
    return flask.send_file(current_app.config['TMPDIR'] + "/" + fileName)

@api.route("/modelInstance")
class ModelInstance(Resource):
  """End point to get the model instance as json"""

  parser = reqparse.RequestParser()
  parser.add_argument("MetadataJson", location = "files", type = FileStorage, required = True, help = "JSON file with simulation data information")
  parser.add_argument("ModelZip", location = "files", type = FileStorage, help = "Zip file containing the extra Modelica files needed for instantiation")
  parser.add_argument("PrettyPrint", location = "form", type = bool, default=False)

  @api.expect(parser)
  def post(self):
    """Simulate the model."""
    args = self.parser.parse_args()
    metaDataJsonFileArg = args["MetadataJson"]
    modelZipFileArg = args["ModelZip"]
    prettyPrintArg = args["PrettyPrint"]

    omc = OMC()
    originalDir = omc.sendCommand("cd()")
    metaDataJson = {}
    file = ""

    status, uploadDirectory, messages, metaDataJson = readMetaDataAndZipFile(omc, metaDataJsonFileArg, modelZipFileArg)
    if not status:
      return setResultJsonAndQuitOMC(omc, originalDir, messages, file)

    # simulate the model
    className = metaDataJson.get("class", "")
    if className:
      modelInstanceJson = omc.sendCommand("getModelInstance({0}, {1})".format(className, util.pythonBoolToModelicaBool(prettyPrintArg)))
      fileHandle, modelInstanceJsonFilePath = tempfile.mkstemp(dir=current_app.config['TMPDIR'], suffix=".json", prefix="modelInstanceJson-")
      try:
        os.write(fileHandle, modelInstanceJson.encode())
      finally:
        os.close(fileHandle)
      messages = "Model instance json is created."
      file = flask.url_for('api.download', FileName="{0}".format(os.path.basename(modelInstanceJsonFilePath)), _external=True)
    else:
      messages = "Class is missing."
      file = ""

    return setResultJsonAndQuitOMC(omc, originalDir, messages, file)