import pytest

def pytest_collection_modifyitems(config, items):
    """
    Hook to add the custom marker metadata into the JUnit XML properties.
    By default pytest doesn't export custom markers into the JUnit XML.
    """
    for item in items:
        marker = item.get_closest_marker("req")
        if marker:
            # We must add property tuple to user_properties which the junit schema reporter natively reads
            req_id = marker.args[0]
            item.user_properties.append(("req", req_id))
