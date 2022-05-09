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
Tests the model instance endpoint with BouncingBall file.
"""

from pathlib import Path
import tempfile
import shutil
import pytest

# get the resources folder in the tests folder
resources = Path(__file__).parent / "resources"

@pytest.mark.skip(reason="getModeInstance API is missing in the docker image.")
def test_simulate(application):
  application.config.update({
    "TMPDIR": tempfile.mkdtemp(prefix='test_model_instance_with_file')
  })

  response = application.test_client().post("/api/modelInstance", data = {
    "MetadataJson": (resources / "FileModelInstance.metadata.json").open("rb"),
    "ModelZip": (resources / "FileModelInstance.zip").open("rb")
  })
  assert response.status_code == 200
  data = response.json
  file = data.get("file", "")
  if not file:
    print(data)
    assert False

  # cleanup
  shutil.rmtree(application.config['TMPDIR'], ignore_errors=True)