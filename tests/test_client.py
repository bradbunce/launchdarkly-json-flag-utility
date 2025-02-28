"""Tests for the LaunchDarkly client."""

import pytest
from ld_json_flag.client import LaunchDarklyClient


def test_tcp_port_json_validation():
    """Test validation of TCP port JSON objects."""
    client = LaunchDarklyClient("fake-key", "fake-project")

    # Valid case
    valid_json = {"tcp_port": 443}
    assert client.validate_tcp_port_json(valid_json) is True

    # Invalid cases
    with pytest.raises(ValueError, match="JSON must be an object"):
        client.validate_tcp_port_json("not an object")

    with pytest.raises(ValueError, match="JSON must contain a tcp_port property"):
        client.validate_tcp_port_json({})

    with pytest.raises(ValueError, match="tcp_port must be an integer"):
        client.validate_tcp_port_json({"tcp_port": "443"})

    with pytest.raises(ValueError, match="tcp_port must be between 0 and 65535"):
        client.validate_tcp_port_json({"tcp_port": -1})

    with pytest.raises(ValueError, match="tcp_port must be between 0 and 65535"):
        client.validate_tcp_port_json({"tcp_port": 65536})
