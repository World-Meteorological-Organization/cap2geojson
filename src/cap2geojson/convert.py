import math
from typing import Union
import xmltodict


def get_properties(alert: dict) -> dict:
    """Creates the properties object for the GeoJSON Feature object from the CAP alert.

    Args:
        alert (dict): The extracted CAP alert object.

    Returns:
        dict: The formatted properties object.
    """
    info = alert["cap:info"]
    return {
        "identifier": alert["cap:identifier"],
        "sender": alert["cap:sender"],
        "sent": alert["cap:sent"],
        "status": alert["cap:status"],
        "msgType": alert["cap:msgType"],
        "scope": alert["cap:scope"],
        "category": info["cap:category"],
        "event": info["cap:event"],
        "urgency": info["cap:urgency"],
        "severity": info["cap:severity"],
        "certainty": info["cap:certainty"],
        "effective": info["cap:effective"],
        "onset": info["cap:onset"],
        "expires": info["cap:expires"],
        "senderName": info["cap:senderName"],
        "headline": info["cap:headline"],
        "description": info["cap:description"],
        "instruction": info["cap:instruction"],
        "web": info["cap:web"],
        "contact": info["cap:contact"],
        "areaDesc": get_area_desc(info["cap:area"]),
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
        return area["cap:areaDesc"]
    return ", ".join([a["cap:areaDesc"] for a in area])


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

    def get_circle_coord(theta: float, x_centre: float,
                         y_centre: float, radius: float) -> list:
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
    if "cap:circle" in single_area:
        # Takes form "x,y r"
        centre, radius = map(float, single_area["cap:circle"].split(" "))
        x_centre, y_centre = centre.split(",")
        # Estimate the circle coordinates with n=100 points
        return get_all_circle_coords(x_centre, y_centre, radius, 100)

    if "cap:polygon" in single_area:
        # Takes form "x,y x,y x,y" but with newlines that need to be removed
        polygon_str = single_area["cap:polygon"].replace("\n", "").split()
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


def to_geojson(xml: bytes) -> dict:
    """Takes the CAP alert XML and converts it to a GeoJSON.

    Args:
        xml (bytes): The CAP XML byte string.

    Returns:
        dict: The final GeoJSON object.
    """
    data = xmltodict.parse(xml)
    alert = data["cap:alert"]

    alert_properties = get_properties(alert)
    alert_geometry = get_geometry(alert["cap:info"]["cap:area"])

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
