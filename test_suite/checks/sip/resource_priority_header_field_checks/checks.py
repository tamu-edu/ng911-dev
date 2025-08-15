import re
from .constants import RESOURCE_PRIORITY_PATTERN


def test_resource_priority(resource_priority_header):
    """
    Test to validate the Resource Priority header.
    """
    try:
        assert resource_priority_header, "FAILED to find Resource Priority header"
        assert re.search(RESOURCE_PRIORITY_PATTERN, resource_priority_header), "FAILED - Resource-Priority wrong value"
        return "PASSED"
    except AssertionError as e:
        return str(e)
