import math
import xmltodict


def get_properties(alert):
    """Creates the properties object for the GeoJSON Feature object from the CAP alert.

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


def get_area_desc(area):
    """Formats the area description for the GeoJSON properties object.

    Args:
        area (dict): The area information of the CAP alert.

    Returns:
        str: The formatted area description.
    """
    if isinstance(area, dict):
        return area["areaDesc"]
    return ", ".join([a["areaDesc"] for a in area])


def get_circle_coord(theta, x_center, y_center, radius):
    """Calculates the x and y coordinates of a point on a circle.

    Args:
        theta (_type_): _description_
        x_center (_type_): _description_
        y_center (_type_): _description_
        radius (_type_): _description_

    Returns:
        tuple: The x and y coordinates of the point, rounded to 5dp.
    """
    x = radius * math.cos(theta) + x_center
    y = radius * math.sin(theta) + y_center
    return (round(x, 5), round(y, 5))


def get_all_circle_coords(x_center, y_center, radius, n_points):
    """
    Estimate the n coordinates of a circle with a given center and radius.

    Args:
        x_center (_type_): _description_
        y_center (_type_): _description_
        radius (_type_): _description_
        n_points (_type_): _description_

    Returns:
        list: The n estimated coordinates of the circle.
    """
    thetas = [i / n_points * math.tau for i in range(n_points)]
    circle_coords = [
        get_circle_coord(theta, x_center, y_center, radius) for theta in thetas
    ]
    return circle_coords


def get_multi_coordinates(area):
    """Formats the coordinates for the GeoJSON MultiPolygon object.

    Args:
        area (dict): The area information of the CAP alert.

    Returns:
        list: The formatted multi-polygon coordinates.
    """
    # Idea: loop over each area object and check if it's "circle" or "polygon"
    # If it's a circle, calculate the circle coordinates and add them to the list
    # If it's a polygon, add the polygon coordinates to the list


def to_geojson(xml):
    """Takes the CAP alert XML and converts it to a GeoJSON.

    Args:
        xml (bytes): The CAP XML byte string.

    Returns:
        dict: The final GeoJSON object.
    """
    data = xmltodict.parse(xml)
    alert = data["alert"]

    alert_properties = get_properties(alert)
    multi_polygon_coordinates = get_multi_coordinates(alert)

    return {
        "type": "FeatureCollection",
        "features": [
            {
                "type": "Feature",
                "properties": alert_properties,
                "geometry": {
                    "type": "MultiPolygon",
                    "coordinates": [multi_polygon_coordinates],
                },
            }
        ],
    }
