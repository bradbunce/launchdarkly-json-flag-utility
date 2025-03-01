"""Tests for the LaunchDarkly client."""

import pytest
from unittest.mock import patch, MagicMock
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


@patch("requests.get")
def test_get_projects(mock_get):
    """Test getting projects."""
    # Mock responses for pagination
    first_page_response = MagicMock()
    first_page_response.status_code = 200
    first_page_response.json.return_value = {
        "items": [
            {"key": "project1", "name": "Project 1"},
            {"key": "project2", "name": "Project 2"},
        ],
        "_links": {
            "next": {"href": "https://app.launchdarkly.com/api/v2/projects?page=2"}
        },
    }

    second_page_response = MagicMock()
    second_page_response.status_code = 200
    second_page_response.json.return_value = {
        "items": [{"key": "project3", "name": "Project 3"}],
        "_links": {},  # No next page
    }

    # Configure mock to return different responses for different URLs
    mock_get.side_effect = [first_page_response, second_page_response]

    # Test function
    client = LaunchDarklyClient("fake-key")
    projects = client.get_projects()

    # Assertions
    assert mock_get.call_count == 2
    mock_get.assert_any_call(
        "https://app.launchdarkly.com/api/v2/projects",
        headers={"Authorization": "fake-key", "Content-Type": "application/json"},
    )
    mock_get.assert_any_call(
        "https://app.launchdarkly.com/api/v2/projects?page=2",
        headers={"Authorization": "fake-key", "Content-Type": "application/json"},
    )

    # Check that all items from both pages are returned
    assert len(projects) == 3
    assert projects[0]["key"] == "project1"
    assert projects[1]["name"] == "Project 2"
    assert projects[2]["key"] == "project3"


@patch("requests.get")
def test_get_environments(mock_get):
    """Test getting environments."""
    # Mock response
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "environments": [
            {"key": "production", "name": "Production"},
            {"key": "staging", "name": "Staging"},
        ]
    }
    mock_get.return_value = mock_response

    # Test function
    client = LaunchDarklyClient("fake-key", "test-project")
    environments = client.get_environments()

    # Assertions
    mock_get.assert_called_once_with(
        "https://app.launchdarkly.com/api/v2/projects/test-project",
        headers={"Authorization": "fake-key", "Content-Type": "application/json"},
    )
    assert len(environments) == 2
    assert environments[0]["key"] == "production"
    assert environments[1]["name"] == "Staging"


@patch("requests.get")
def test_get_feature_flags(mock_get):
    """Test getting feature flags."""
    # Mock responses for pagination
    first_page_response = MagicMock()
    first_page_response.status_code = 200
    first_page_response.json.return_value = {
        "items": [
            {"key": "flag1", "name": "Flag 1", "kind": "json"},
            {"key": "flag2", "name": "Flag 2", "kind": "boolean"},
        ],
        "_links": {
            "next": {
                "href": "https://app.launchdarkly.com/api/v2/flags/test-project?page=2"
            }
        },
    }

    second_page_response = MagicMock()
    second_page_response.status_code = 200
    second_page_response.json.return_value = {
        "items": [
            {"key": "flag3", "name": "Flag 3", "kind": "json"},
        ],
        "_links": {},  # No next page
    }

    # Configure mock to return different responses for different URLs
    mock_get.side_effect = [first_page_response, second_page_response]

    # Test function
    client = LaunchDarklyClient("fake-key", "test-project")
    flags = client.get_feature_flags()

    # Assertions
    assert mock_get.call_count == 2
    mock_get.assert_any_call(
        "https://app.launchdarkly.com/api/v2/flags/test-project",
        headers={"Authorization": "fake-key", "Content-Type": "application/json"},
    )
    mock_get.assert_any_call(
        "https://app.launchdarkly.com/api/v2/flags/test-project?page=2",
        headers={"Authorization": "fake-key", "Content-Type": "application/json"},
    )

    # Check that all items from both pages are returned
    assert len(flags) == 3
    assert flags[0]["key"] == "flag1"
    assert flags[1]["kind"] == "boolean"
    assert flags[2]["key"] == "flag3"


@patch("requests.get")
def test_get_feature_flag(mock_get):
    """Test getting a specific feature flag."""
    # Mock response
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "key": "test-flag",
        "name": "Test Flag",
        "kind": "json",
        "variations": [{"name": "Production", "value": {"tcp_port": 443}}],
    }
    mock_get.return_value = mock_response

    # Test function
    client = LaunchDarklyClient("fake-key", "test-project")
    flag = client.get_feature_flag("test-flag")

    # Assertions
    mock_get.assert_called_once_with(
        "https://app.launchdarkly.com/api/v2/flags/test-project/test-flag",
        headers={"Authorization": "fake-key", "Content-Type": "application/json"},
    )
    assert flag["key"] == "test-flag"
    assert flag["variations"][0]["value"]["tcp_port"] == 443


@patch("requests.post")
def test_create_feature_flag(mock_post):
    """Test creating a feature flag."""
    # Mock response
    mock_response = MagicMock()
    mock_response.status_code = 201
    mock_response.json.return_value = {
        "key": "test-flag",
        "name": "Test Flag",
        "kind": "json",
    }
    mock_post.return_value = mock_response

    # Test data
    variations = [
        {
            "name": "Production",
            "description": "Production configuration",
            "value": {"tcp_port": 443},
        },
        {
            "name": "Development",
            "description": "Development configuration",
            "value": {"tcp_port": 8080},
        },
    ]

    # Test function
    client = LaunchDarklyClient("fake-key", "test-project")
    result = client.create_feature_flag("test-flag", "Test Flag", variations)

    # Assertions
    mock_post.assert_called_once()
    call_args = mock_post.call_args
    assert call_args[0][0] == "https://app.launchdarkly.com/api/v2/flags/test-project"
    assert call_args[1]["headers"] == {
        "Authorization": "fake-key",
        "Content-Type": "application/json",
    }

    # Check payload
    payload = call_args[1]["json"]
    assert payload["key"] == "test-flag"
    assert payload["name"] == "Test Flag"
    assert payload["kind"] == "json"
    assert len(payload["variations"]) == 2
    assert payload["variations"][0]["value"]["tcp_port"] == 443
    assert payload["variations"][1]["value"]["tcp_port"] == 8080

    # Check result
    assert result["key"] == "test-flag"


@patch("requests.patch")
def test_update_flag_variations(mock_patch):
    """Test updating flag variations."""
    # Mock response
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "key": "test-flag",
        "name": "Test Flag",
        "kind": "json",
    }
    mock_patch.return_value = mock_response

    # Test data
    variations = [
        {
            "name": "Production",
            "description": "Production configuration",
            "value": {"tcp_port": 443},
        },
        {
            "name": "Development",
            "description": "Development configuration",
            "value": {"tcp_port": 8080},
        },
    ]

    # Test function
    client = LaunchDarklyClient("fake-key", "test-project")
    result = client.update_flag_variations("test-flag", variations)

    # Assertions
    mock_patch.assert_called_once()
    call_args = mock_patch.call_args
    assert (
        call_args[0][0]
        == "https://app.launchdarkly.com/api/v2/flags/test-project/test-flag"
    )
    assert call_args[1]["headers"] == {
        "Authorization": "fake-key",
        "Content-Type": "application/json",
    }

    # Check payload
    payload = call_args[1]["json"]
    assert payload["comment"] == "Updated flag variations via LD JSON Flag Utility"
    assert payload["patch"][0]["op"] == "replace"
    assert payload["patch"][0]["path"] == "/variations"
    assert len(payload["patch"][0]["value"]) == 2
    assert payload["patch"][0]["value"][0]["value"]["tcp_port"] == 443
    assert payload["patch"][0]["value"][1]["value"]["tcp_port"] == 8080

    # Check result
    assert result["key"] == "test-flag"


@patch("requests.patch")
def test_configure_environment_targeting(mock_patch):
    """Test configuring environment targeting."""
    # Mock response
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "key": "test-flag",
        "name": "Test Flag",
        "kind": "json",
    }
    mock_patch.return_value = mock_response

    # Test data
    targeting_rules = [
        {
            "description": "Test rule",
            "clauses": [{"attribute": "groups", "op": "in", "values": ["test-group"]}],
            "variation": 1,
        }
    ]

    # Test function
    client = LaunchDarklyClient("fake-key", "test-project")
    result = client.configure_environment_targeting(
        "test-flag", "production", targeting_rules
    )

    # Assertions
    mock_patch.assert_called_once()
    call_args = mock_patch.call_args
    assert (
        call_args[0][0]
        == "https://app.launchdarkly.com/api/v2/flags/test-project/test-flag/environments/production"
    )
    assert call_args[1]["headers"] == {
        "Authorization": "fake-key",
        "Content-Type": "application/json",
    }

    # Check payload
    payload = call_args[1]["json"]
    assert payload["instructions"][0]["kind"] == "replaceRule"
    assert len(payload["instructions"][0]["rules"]) == 1
    assert payload["instructions"][0]["rules"][0]["description"] == "Test rule"
    assert payload["instructions"][0]["rules"][0]["variation"] == 1

    # Check result
    assert result["key"] == "test-flag"


# Tests for the validation functionality
@patch("ld_json_flag.interactive.edit_json_in_editor")
@patch("ld_json_flag.interactive.input")
@patch("builtins.print")
def test_validate_flags_workflow_valid_flags(mock_print, mock_input, mock_editor):
    """Test validating flags when all flags are valid."""
    # Create a mock client
    client = MagicMock()

    # Mock client.get_feature_flags to return a list of flags
    client.get_feature_flags.return_value = [{"key": "flag1", "name": "Flag 1"}]

    # Mock client.get_feature_flag to return flag details
    client.get_feature_flag.return_value = {
        "key": "flag1",
        "name": "Flag 1",
        "variations": [{"name": "Variation 1", "value": {"tcp_port": 443}}],
    }

    # Mock client.validate_tcp_port_json to always return True (valid)
    client.validate_tcp_port_json.return_value = True

    # Set project_key
    client.project_key = "test-project"

    # Call the function
    from ld_json_flag.interactive import validate_flags_workflow

    result = validate_flags_workflow(client)

    # Assertions
    assert result is True
    client.get_feature_flags.assert_called_once_with("test-project")
    client.get_feature_flag.assert_called_once_with("flag1", "test-project")
    client.validate_tcp_port_json.assert_called_once()

    # Check that the success message was printed
    mock_print.assert_any_call("\n✅ All JSON feature flags are valid!")


@patch("ld_json_flag.interactive.edit_json_in_editor")
@patch("ld_json_flag.interactive.input")
@patch("builtins.print")
def test_validate_flags_workflow_invalid_flags_no_fix(
    mock_print, mock_input, mock_editor
):
    """Test validating flags when there are invalid flags but fix is not enabled."""
    # Create a mock client
    client = MagicMock()

    # Mock client.get_feature_flags to return a list of flags
    client.get_feature_flags.return_value = [{"key": "flag1", "name": "Flag 1"}]

    # Mock client.get_feature_flag to return flag details
    client.get_feature_flag.return_value = {
        "key": "flag1",
        "name": "Flag 1",
        "variations": [
            {
                "name": "Variation 1",
                "value": {
                    "tcp_port": "invalid"
                },  # Invalid port (string instead of int)
            }
        ],
    }

    # Mock client.validate_tcp_port_json to raise ValueError for invalid port
    client.validate_tcp_port_json.side_effect = ValueError(
        "tcp_port must be an integer"
    )

    # Set project_key
    client.project_key = "test-project"

    # Call the function
    from ld_json_flag.interactive import validate_flags_workflow

    result = validate_flags_workflow(client, fix_invalid=False)

    # Assertions
    assert result is False
    client.get_feature_flags.assert_called_once_with("test-project")
    client.get_feature_flag.assert_called_once_with("flag1", "test-project")
    client.validate_tcp_port_json.assert_called_once()

    # Check that the error message was printed
    mock_print.assert_any_call("\n❌ Found 1 invalid JSON feature flags.")
    mock_print.assert_any_call("Run with --fix to fix invalid flags.")


@patch("ld_json_flag.interactive.edit_json_in_editor")
@patch("ld_json_flag.interactive.input")
@patch("builtins.print")
def test_validate_flags_workflow_invalid_flags_with_fix(
    mock_print, mock_input, mock_editor
):
    """Test validating and fixing invalid flags."""
    # Create a mock client
    client = MagicMock()

    # Mock client.get_feature_flags to return a list of flags
    client.get_feature_flags.return_value = [{"key": "flag1", "name": "Flag 1"}]

    # Mock client.get_feature_flag to return flag details
    client.get_feature_flag.return_value = {
        "key": "flag1",
        "name": "Flag 1",
        "variations": [
            {
                "name": "Variation 1",
                "value": {
                    "tcp_port": "invalid"
                },  # Invalid port (string instead of int)
            }
        ],
    }

    # Set up the validation to fail on first call but succeed after editing
    def validate_side_effect(value):
        if value == {"tcp_port": "invalid"}:
            raise ValueError("tcp_port must be an integer")
        return True

    client.validate_tcp_port_json.side_effect = validate_side_effect

    # Mock the editor to return fixed variations
    mock_editor.return_value = [
        {"name": "Variation 1", "value": {"tcp_port": 443}}  # Fixed port (int)
    ]

    # Mock input to confirm the update
    mock_input.return_value = "y"

    # Set project_key
    client.project_key = "test-project"

    # Call the function
    from ld_json_flag.interactive import validate_flags_workflow

    result = validate_flags_workflow(client, fix_invalid=True)

    # Assertions
    assert result is True
    client.get_feature_flags.assert_called_once_with("test-project")
    client.get_feature_flag.assert_called_once_with("flag1", "test-project")
    mock_editor.assert_called_once()
    client.update_flag_variations.assert_called_once()

    # Check that the success message was printed
    mock_print.assert_any_call("\n❌ Found 1 invalid JSON feature flags.")
    mock_print.assert_any_call("\nFixing invalid flags...")
    mock_print.assert_any_call("✅ Successfully updated variations for flag 'flag1'")
