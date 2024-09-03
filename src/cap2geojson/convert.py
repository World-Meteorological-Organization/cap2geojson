import geojson
import json
import logging
import math
from typing import Generator, Union
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
        "identifier": alert.get("identifier"),
        "sender": alert.get("sender"),
        "sent": alert.get("sent"),
        "status": alert.get("status"),
        "msgType": alert.get("msgType"),
        "scope": alert.get("scope"),
        "category": info.get("category"),
        "event": info.get("event"),
        "urgency": info.get("urgency"),
        "severity": info.get("severity"),
        "certainty": info.get("certainty"),
        "effective": info.get("effective"),
        "onset": info.get("onset"),
        "expires": info.get("expires"),
        "senderName": info.get("senderName"),
        "headline": info.get("headline"),
        "description": info.get("description"),
        "instruction": info.get("instruction"),
        "web": info.get("web"),
        "contact": info.get("contact"),
        "areaDesc": get_area_desc(info.get("area")),
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


def get_circle_coords(
    x_centre: float, y_centre: float, radius: float, n_points: int
) -> Generator[list, None, None]:
    """
    Estimate the n+1 coordinates of a circle with a given centre and radius.

    Args:
        x_centre (float): The longitude of the circle's centre.
        y_centre (float): The latitude of the circle's centre.
        radius (float): The radius of the circle.
        n_points (int): The number of edges in the n-gon to approximate
        the circle.

    Returns:
        Generator: Yield the n+1 estimated coordinates of the circle.
    """
    # Generate thetas for the n-gon
    thetas = [i / n_points * math.tau for i in range(n_points)]
    # Add theta = 0 to the end to ensure the circle is closed
    thetas.append(0)

    for theta in thetas:
        x = radius * math.cos(theta) + x_centre
        y = radius * math.sin(theta) + y_centre
        # Round to 5 decimal places to prevent excessive precision
        yield [round(x, 5), round(y, 5)]


def ensure_counter_clockwise(coords: list) -> list:
    """
    Ensure the polygon coordinates are in counter-clockwise order,
    a.k.a. the right-hand rule.

    Args:
        coords (list): List of coordinate pairs.

    Returns:
        list: List of coordinate pairs in counter-clockwise order.
    """

    def clockwise(coords: list) -> bool:
        """Calculate (double) the signed area of the polygon, to help
        determine the order of the coordinates."""
        area = 0
        n = len(coords)
        for i in range(n):
            x1, y1 = coords[i]
            x2, y2 = coords[(i + 1) % n]
            area += (x1 * y2) - (x2 * y1)
        return area < 0

    if clockwise(coords):
        coords.reverse()
    return coords


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
        centre, radius = single_area["circle"].split(" ")
        radius = float(radius)
        x_centre, y_centre = map(float, centre.split(","))
        # Estimate the circle coordinates with n=100 points
        return list(get_circle_coords(x_centre, y_centre, radius, 100))

    if "polygon" in single_area:
        # Takes form "x,y x,y x,y" but with newlines that need to be removed
        polygon_str = single_area["polygon"].replace("\n", "").split()
        polygon_list = [list(map(float, coord.split(","))) for coord in polygon_str] # noqa
        return ensure_counter_clockwise(polygon_list)

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
            "coordinates": [[get_polygon_coordinates(a)] for a in area],
        }
    return {
        "type": "Polygon",
        "coordinates": [get_polygon_coordinates(area)],
    }


def preprocess_alert(xml: str) -> str:
    """Removes the 'cap:' prefix from the XML string tags,
    so for example '<cap:info>' becomes '<info>' and '</cap:info>'
    becomes '</info>'.

    Args:
        xml (str): The CAP XML string.

    Returns:
        str: The XML string with the 'cap:' prefix removed from the tags.
    """
    return re.sub(r"<(/?)cap:(\w+)", r"<\1\2", xml)


def to_geojson(xml: str) -> str:
    """Takes the CAP alert XML and converts it to a GeoJSON.

    Args:
        xml (str): The CAP XML string.

    Returns:
        str: The final GeoJSON object stringified.
    """
    processed_xml = preprocess_alert(xml)

    try:
        data = xmltodict.parse(processed_xml)
    except Exception as e:
        logger.error(f"Error parsing XML: {e}")
        raise

    alert = data.get("alert", {})
    if not alert:
        logger.error("No alert object found in the XML.")
        raise ValueError("No alert object found in the XML.")

    alert_properties = get_properties(alert)

    area = alert.get("info", {}).get("area")
    if not area:
        logger.error("No area object found in the alert.")
        raise ValueError("No area object found in the alert.")

    alert_geometry = get_geometry(area)

    result = json.dumps(
        {
            "type": "FeatureCollection",
            "features": [
                {
                    "type": "Feature",
                    "properties": alert_properties,
                    "geometry": alert_geometry,
                }
            ],
        },
        indent=4,
    )

    try:
        geojson.loads(result)
    except Exception as e:
        logger.error(f"Error converting to GeoJSON: {e}")
        raise

    return result
