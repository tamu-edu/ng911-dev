import math
from math import radians, sin, cos, sqrt, atan2
from shapely.geometry import Point, Polygon
from geopy.distance import geodesic
import xml.etree.ElementTree as ET


def haversine_distance(coord1: str, coord2: str) -> float:
    """
    Calculates distance between points
    @param coord1: Point #1
    @param coord2: Point #1
    @return: distance in meters
    """
    # Radius of the Earth in meters
    radius = 6371000
    lat1, lon1 = coord1
    lat2, lon2 = coord2

    # Convert latitude and longitude from degrees to radians
    lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])

    # Compute differences
    dlat = lat2 - lat1
    dlon = lon2 - lon1

    # Haversine formula
    a = sin(dlat / 2) ** 2 + cos(lat1) * cos(lat2) * sin(dlon / 2) ** 2
    c = 2 * atan2(sqrt(a), sqrt(1 - a))
    return radius * c


def validate_coordinate(coord_str: str) -> tuple or None:
    """
    Coordinates format validator
    @param coord_str: Coordinates in string representation
    @return: Coordinates in tuple representation
    """
    try:
        lat, lon = map(float, coord_str.split())
        return lat, lon
    except:
        return None


def extract_shape_data(xml_file: str) -> dict:
    """
    Extracts polygon tipe data and area from xml-formated string
    @param xml_file: XML data in string representation
    @return: Dictionary with 'type', 'coordinates' and 'radius' data
    """
    root = ET.fromstring(xml_file)

    namespaces = {
        'lf': 'urn:ietf:params:xml:ns:location-filter',
        'gs': 'http://www.opengis.net/pidflo/1.0',
        'gml': 'http://www.opengis.net/gml'
    }

    shapes = {}

    for circle in root.findall('.//gs:Circle', namespaces):
        shape_type = 'Circle'
        pos = circle.find('gml:pos', namespaces)
        radius = circle.find('gs:radius', namespaces)

        if pos is not None and radius is not None:
            coordinates = pos.text.strip()
            radius_value = radius.text.strip()
            shapes['type'] = shape_type
            shapes['coordinates'] = coordinates
            shapes['radius'] = radius_value

    # Add parsing logic here for other shapes like Polygon if needed

    return shapes


def is_point_in_shape(shape: dict, point_str: str) -> dict:
    """
    Check if a point (as a string) is inside a shape and return area + containment result.
    @param shape: Dictionary with keys:
                      - type: 'Circle' or 'Polygon'
                      - coordinates: str (space-separated for Circle, semicolon-separated pairs for Polygon)
                      - radius: str or float (required for Circle, in meters)

    @param point_str: A string like 'lat lon' representing the test point.

    @return:
        dict: {
            'area': area in square meters (float),
            'contains_point': True or False
        }
    """
    shape_type = shape['type']
    coordinates = shape['coordinates']
    lat_str, lon_str = point_str.strip().split()
    point = (float(lat_str), float(lon_str))

    if shape_type == 'Circle':
        center_lat, center_lon = map(float, coordinates.split())
        radius = float(shape['radius'])  # in meters

        # Distance from center to point
        distance = geodesic((center_lat, center_lon), point).meters
        contains = distance <= radius

    elif shape_type == 'Polygon':
        # Coordinates string: "lat1 lon1; lat2 lon2; ..."
        points = [
            tuple(map(float, coord.split()))
            for coord in coordinates.strip().split(';')
        ]
        polygon = Polygon([(lon, lat) for lat, lon in points])  # Shapely uses (x, y) = (lon, lat)

        test_point = Point(point[1], point[0])  # (lon, lat)
        contains = polygon.contains(test_point)

    else:
        raise ValueError(f"Unsupported shape type: {shape_type}")

    return contains


def is_valid_distance_between_points(points: list, threshold: int) -> bool:
    """
    Verifies if distance between point are in threshold value
    @param points: List of points
    @param threshold: Threshold taken from SIP SUBSCRIBE message
    @return: True of False
    """
    # Filter and parse valid coordinates
    valid_points = [validate_coordinate(p) for p in points]
    valid_points = [p for p in valid_points if p is not None]

    if len(valid_points) < 2:
        return False
    # Check pairwise distances
    for i in range(len(points) - 1):
        dist = haversine_distance(valid_points[i], valid_points[i + 1])
        if dist <= threshold:
            return False
    return True


def is_valid_speed_between_messages(speed_list: list, threshold: int) -> bool:
    """
    Verifies if speed values mentioned in SIP NOTIFY messages point are below threshold value
    @param speed_list: List with speed data
    @param threshold: Threshold taken from SIP SUBSCRIBE message
    @return: True of False
    """
    # Check pairwise speed
    for i in range(len(speed_list) - 1):
        diff = int(speed_list[i + 1]) - int(speed_list[i])
        if diff <= threshold:
            return False
    return True