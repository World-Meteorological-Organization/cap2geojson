###############################################################################
#
# Licensed to the Apache Software Foundation (ASF) under one
# or more contributor license agreements.  See the NOTICE file
# distributed with this work for additional information
# regarding copyright ownership.  The ASF licenses this file
# to you under the Apache License, Version 2.0 (the
# "License"); you may not use this file except in compliance
# with the License.  You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing,
# software distributed under the License is distributed on an
# "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
# KIND, either express or implied.  See the License for the
# specific language governing permissions and limitations
# under the License.
#
###############################################################################

import logging
import pytest

from cap2geojson.convert import (
    get_properties,
    get_circle_coords,
    ensure_counter_clockwise,
    get_polygon_coordinates,
    get_geometry,
    preprocess_alert,
    to_geojson,
)

LOGGER = logging.getLogger(__name__)


@pytest.fixture
def sc_alert():
    with open("tests/input/sc.xml", "r") as f:
        return f.read()


def test_to_geojson(sc_alert):
    with open("tests/output/sc.geojson", "r") as f:
        expected = f.read()

    assert to_geojson(sc_alert) == expected
