import logging
import math
from typing import Union
import re
import xmltodict

logger = logging.getLogger(__name__)


def get_properties(alert: dict) -> dict:
    """Creates the properties object for the GeoJSON Feature object
    from the CAP alert.

    Args:
        alert (dict): The extracted CAP alert object.

    Returns:
        dict: The formatted properties object.
    """
    info = alert["info"]
    return {
        "identifier": alert["identifier"],
        "sender": alert["sender"],
        "sent": alert["sent"],
        "status": alert["status"],
        "msgType": alert["msgType"],
        "scope": alert["scope"],
        "category": info["category"],
        "event": info["event"],
        "urgency": info["urgency"],
        "severity": info["severity"],
        "certainty": info["certainty"],
        "effective": info["effective"],
        "onset": info["onset"],
        "expires": info["expires"],
        "senderName": info["senderName"],
        "headline": info["headline"],
        "description": info["description"],
        "instruction": info["instruction"],
        "web": info["web"],
        "contact": info["contact"],
        "areaDesc": get_area_desc(info["area"]),
    }


def get_area_desc(area: Union[dict, list]) -> str:
    """Formats the area description so that if the area is a list of areas,
    they are concatenated into a single string delimited by commas.

    Args:
        area (Union[dict, list]): The area information of the CAP alert.

    Returns:
        str: The formatted area description.
    """
    if isinstance(area, dict):
        return area["areaDesc"]
    return ", ".join([a["areaDesc"] for a in area])


def get_all_circle_coords(
    x_centre: float, y_centre: float, radius: float, n_points: int
) -> list:
    """
    Estimate the n coordinates of a circle with a given centre and radius.

    Args:
        x_centre (float): The longitude of the circle's centre.
        y_centre (float): The latitude of the circle's centre.
        radius (float): The radius of the circle.
        n_points (int): The number of edges in the n-gon to approximate
        the circle.

    Returns:
        list: The n estimated coordinates of the circle.
    """

    def get_circle_coord(
        theta: float, x_centre: float, y_centre: float, radius: float
    ) -> list:
        x = radius * math.cos(theta) + x_centre
        y = radius * math.sin(theta) + y_centre
        # Round to 5 decimal places to prevent excessive precision
        return [round(x, 5), round(y, 5)]

    thetas = [i / n_points * math.tau for i in range(n_points)]
    circle_coords = [
        get_circle_coord(theta, x_centre, y_centre, radius) for theta in thetas
    ]
    return circle_coords


def get_polygon_coordinates(single_area: dict) -> list:
    """Formats the coordinates for the GeoJSON Polygon object.

    Args:
        single_area (dict): The area information of one simply-connected
        region affected by the CAP alert.

    Returns:
        list: The list of polygon coordinate pairs.
    """
    if "circle" in single_area:
        # Takes form "x,y r"
        centre, radius = map(float, single_area["circle"].split(" "))
        x_centre, y_centre = centre.split(",")
        # Estimate the circle coordinates with n=100 points
        return get_all_circle_coords(x_centre, y_centre, radius, 100)

    if "polygon" in single_area:
        # Takes form "x,y x,y x,y" but with newlines that need to be removed
        polygon_str = single_area["polygon"].replace("\n", "").split()
        return [list(map(float, coord.split(","))) for coord in polygon_str]

    return []


def get_geometry(area: Union[dict, list]) -> dict:
    """Creates the geometry object for the GeoJSON Feature object.

    Args:
        area (Union[dict, list]): The area(s) affected by the CAP alert.
        If there are multiple areas, they are in a list and will be formatted
        as a MultiPolygon.

    Returns:
        dict: The formatted geometry object.
    """
    if isinstance(area, list):
        return {
            "type": "MultiPolygon",
            "coordinates": [get_polygon_coordinates(a) for a in area],
        }
    return {
        "type": "Polygon",
        "coordinates": get_polygon_coordinates(area),
    }


def handle_namespace(xml: str) -> str:
    """Removes the 'cap:' prefix from the XML string tags,
    so for example '<cap:info>' becomes '<info>' and '</cap:info>'
    becomes '</info>'.

    Args:
        xml (str): The CAP XML string.

    Returns:
        str: The XML string with the 'cap:' prefix removed from the tags.
    """
    xml = re.sub(r"<cap:(\w+)>", r"<\1>", xml)
    xml = re.sub(r"</cap:(\w+)>", r"</\1>", xml)
    return xml


def to_geojson(xml: str) -> dict:
    """Takes the CAP alert XML and converts it to a GeoJSON.

    Args:
        xml (str): The CAP XML string.

    Returns:
        dict: The final GeoJSON object.
    """
    xml = handle_namespace(xml)
    data = xmltodict.parse(xml)

    alert = data["alert"]
    alert_properties = get_properties(alert)
    alert_geometry = get_geometry(alert["info"]["area"])

    return {
        "type": "FeatureCollection",
        "features": [
            {
                "type": "Feature",
                "properties": alert_properties,
                "geometry": alert_geometry,
            }
        ],
    }
