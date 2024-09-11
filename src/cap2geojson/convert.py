import json
import logging
import re
from typing import Generator, Union

import geojson
import xmltodict
from pyproj import Transformer
from shapely.geometry import Point
from shapely.geometry.polygon import orient
from shapely.ops import transform as transform_bufr

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
    x_centre: float, y_centre: float, radius: float
) -> Generator[list, None, None]:
    """
    Estimate the n+1 coordinates of a circle with a given centre and radius
    using the azimuthal equidistant projection.

    Args:
        x_centre (float): The longitude of the circle's centre.
        y_centre (float): The latitude of the circle's centre.
        radius (float): The radius of the circle in kilometres.

    Returns:
        Generator: Yield the n+1 estimated coordinates of the circle.
    """
    # Validate latitude and longitude
    if not (-90 <= y_centre <= 90):
        raise ValueError(
            f"Invalid latitude value: {y_centre}. Must be between -90 and 90 degrees." # noqa
        )
    if not (-180 <= x_centre <= 180):
        raise ValueError(
            f"Invalid longitude value: {x_centre}. Must be between -180 and 180 degrees." # noqa
        )

    # Create local azimuthal equidistant projection
    local_azimuthal_projection = (
        f"+proj=aeqd +R=6371000 +units=m +lat_0={y_centre} +lon_0={x_centre}"
    )
    wgs84_to_aeqd = Transformer.from_proj(
        "+proj=longlat +datum=WGS84 +no_defs", local_azimuthal_projection
    )
    aeqd_to_wgs84 = Transformer.from_proj(
        local_azimuthal_projection, "+proj=longlat +datum=WGS84 +no_defs"
    )

    # Transform the center point to the local projection
    point_transformed = Point(wgs84_to_aeqd.transform(x_centre, y_centre))

    # Create a buffer around the transformed point, with radius in metres
    buffer = point_transformed.buffer(radius*1000)

    # Transform the buffer back to WGS84 coordinates
    circle = transform_bufr(aeqd_to_wgs84.transform, buffer)

    # Ensure the coordinates follow the right-hand rule (counter-clockwise)
    circle = orient(circle, sign=1.0)

    # Extract the coordinates from the transformed buffer
    for coord in circle.exterior.coords:
        yield [round(coord[0], 5), round(coord[1], 5)]


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
        # Takes form "y,x r"
        centre, radius = single_area["circle"].split(" ")
        radius = float(radius)
        y_centre, x_centre = map(float, centre.split(","))
        # Estimate the circle coordinates with n=100 points
        return list(get_circle_coords(x_centre, y_centre, radius))

    if "polygon" in single_area:
        # Takes form "y,x y,x y,x". So, split on whitespace, then comma, and
        # reverse the order of the coordinates to be (x, y).
        polygon_str = single_area["polygon"].replace("\n", "").split()
        polygon_list = [
            list(map(float, coord.split(",")[::-1])) for coord in polygon_str
        ]  # noqa
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


def to_geojson(xml: str) -> dict:
    """Takes the CAP alert XML and converts it to a GeoJSON.

    Args:
        xml (str): The CAP XML string.

    Returns:
        str: The final GeoJSON object.
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

    result = {
        "type": "FeatureCollection",
        "features": [
            {
                "type": "Feature",
                "properties": alert_properties,
                "geometry": alert_geometry,
            }
        ],
    }

    try:
        # Verify the GeoJSON is valid
        geojson.loads(json.dumps(result))
    except Exception as e:
        logger.error(f"Error converting to GeoJSON: {e}")
        raise

    return result
