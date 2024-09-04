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

import json
import logging
import pytest
import time

from cap2geojson.convert import (
    get_circle_coords,
    ensure_counter_clockwise,
    get_polygon_coordinates,
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


@pytest.fixture
def circle():
    return {
        "x_centre": 5.0,
        "y_centre": 3.0,
        "radius": 7.0,
    }


def test_circle_coords(circle):
    assert list(get_circle_coords(
        circle["x_centre"], circle["y_centre"], circle["radius"], 10
    )) == [
        [12.0, 3.0],
        [10.66312, 7.1145],
        [7.16312, 9.6574],
        [2.83688, 9.6574],
        [-0.66312, 7.1145],
        [-2.0, 3.0],
        [-0.66312, -1.1145],
        [2.83688, -3.6574],
        [7.16312, -3.6574],
        [10.66312, -1.1145],
        [12.0, 3.0],
    ]


@pytest.fixture
def circle_area():
    return {
        "circle": "5.0,3.0 7.0",
    }


def test_estimate_polygon(circle_area):
    with open("tests/output/circle_estimation.json", "r") as f:
        expected = json.load(f)
    assert get_polygon_coordinates(circle_area) == expected


@pytest.fixture
def small_left_hand_polygon():
    return [[1.0, 1.0], [1.0, 2.0], [2.0, 2.0], [2.0, 1.0]]


@pytest.fixture
def small_right_hand_polygon():
    return [[61.0, -8.4], [50.4, 7.8], [50.8, -12.7], [61.0, -8.4]]


def test_make_right_hand(small_left_hand_polygon):
    original = small_left_hand_polygon.copy()
    result = ensure_counter_clockwise(small_left_hand_polygon)
    assert result == original[::-1]


def test_keep_right_hand(small_right_hand_polygon):
    original = small_right_hand_polygon.copy()
    result = ensure_counter_clockwise(small_right_hand_polygon)
    assert original == result


@pytest.fixture
def large_left_hand_polygon():
    with open("tests/input/large_left_hand_polygon.json", "r") as f:
        return json.load(f)


def test_make_large_left_hand(large_left_hand_polygon):
    original = large_left_hand_polygon.copy()
    start_time = time.time()
    result = ensure_counter_clockwise(large_left_hand_polygon) # noqa
    end_time = time.time()

    assert result == original[::-1]
    assert end_time - start_time < 1.0


@pytest.fixture
def xml_with_cap_tags():
    with open("tests/input/tg.xml", "r", encoding="utf-8") as f:
        return f.read()


@pytest.fixture
def xml_without_cap_tags():
    with open("tests/input/es.xml", "r", encoding="utf-8") as f:
        return f.read()


def test_preprocessing(xml_with_cap_tags, xml_without_cap_tags):
    with open("tests/output/tg_preprocessed.xml", "r", encoding="utf-8") as f:
        expected = f.read()
    assert preprocess_alert(xml_with_cap_tags) == expected
    assert preprocess_alert(xml_without_cap_tags) == xml_without_cap_tags
