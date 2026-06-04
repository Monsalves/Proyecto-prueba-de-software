import pytest

def pytest_configure(config):
    config.addinivalue_line("markers", "test_id(id): ID of the test case")

def pytest_json_runtest_metadata(item, call):
    if call.when == 'setup':
        marker = item.get_closest_marker("test_id")
        if marker:
            return {"test_id": marker.args[0]}
