"""Tests for the interactive functionality."""

from unittest.mock import patch, MagicMock, call
import pytest
from ld_json_flag.interactive import (
    select_from_list,
    select_project,
    select_flag,
    edit_json_in_editor,
    update_flag_variations_workflow,
    create_flag_workflow,
    interactive_workflow,
    validate_flags_workflow,
)


@patch("builtins.input")
@patch("builtins.print")
def test_select_from_list_valid_choice(mock_print, mock_input):
    """Test selecting a valid item from a list."""
    # Setup
    items = ["item1", "item2", "item3"]
    mock_input.return_value = "2"  # Select the second item

    # Call the function
    result = select_from_list(items, "Select an item:")

    # Assertions
    assert result == "item2"
    mock_print.assert_any_call("Select an item:")
    mock_print.assert_any_call("1. item1")
    mock_print.assert_any_call("2. item2")
    mock_print.assert_any_call("3. item3")


@patch("builtins.input")
@patch("builtins.print")
def test_select_from_list_quit(mock_print, mock_input):
    """Test quitting the selection."""
    # Setup
    items = ["item1", "item2", "item3"]
    mock_input.return_value = "q"  # Quit

    # Call the function
    result = select_from_list(items, "Select an item:")

    # Assertions
    assert result is None
    mock_print.assert_any_call("Select an item:")


@patch("builtins.input")
@patch("builtins.print")
def test_select_from_list_invalid_choice(mock_print, mock_input):
    """Test selecting an invalid item from a list."""
    # Setup
    items = ["item1", "item2", "item3"]
    mock_input.side_effect = ["4", "2"]  # First invalid, then valid

    # Call the function
    result = select_from_list(items, "Select an item:")

    # Assertions
    assert result == "item2"
    mock_print.assert_any_call("Please enter a number between 1 and 3")


@patch("builtins.input")
@patch("builtins.print")
def test_select_from_list_non_numeric(mock_print, mock_input):
    """Test entering a non-numeric value."""
    # Setup
    items = ["item1", "item2", "item3"]
    mock_input.side_effect = ["abc", "2"]  # First non-numeric, then valid

    # Call the function
    result = select_from_list(items, "Select an item:")

    # Assertions
    assert result == "item2"
    mock_print.assert_any_call("Please enter a valid number")


@patch("ld_json_flag.interactive.select_from_list")
def test_select_project(mock_select_from_list):
    """Test selecting a project."""
    # Setup
    client = MagicMock()
    client.get_projects.return_value = [
        {"key": "project1", "name": "Project 1"},
        {"key": "project2", "name": "Project 2"},
    ]
    mock_select_from_list.return_value = {"key": "project1", "name": "Project 1"}

    # Call the function
    result = select_project(client)

    # Assertions
    assert result == "project1"
    client.get_projects.assert_called_once()
    mock_select_from_list.assert_called_once()


@patch("ld_json_flag.interactive.select_from_list")
def test_select_flag(mock_select_from_list):
    """Test selecting a flag."""
    # Setup
    client = MagicMock()
    client.get_feature_flags.return_value = [
        {"key": "flag1", "name": "Flag 1"},
        {"key": "flag2", "name": "Flag 2"},
    ]
    client.get_feature_flag.side_effect = lambda key, project_key: {
        "flag1": {"key": "flag1", "variations": [{"value": {}}]},
        "flag2": {"key": "flag2", "variations": [{"value": {"tcp_port": 443}}]},
    }[key]
    mock_select_from_list.return_value = {"key": "flag2", "name": "Flag 2"}

    # Call the function
    result = select_flag(client, "test-project")

    # Assertions
    assert result == "flag2"
    client.get_feature_flags.assert_called_once_with("test-project")
    mock_select_from_list.assert_called_once()


@patch("ld_json_flag.interactive.os.unlink")
@patch("ld_json_flag.interactive.subprocess.call")
@patch("ld_json_flag.interactive.tempfile.NamedTemporaryFile")
@patch("builtins.open")
@patch("builtins.print")
def test_edit_json_in_editor(
    mock_print, mock_open, mock_tempfile, mock_subprocess, mock_unlink
):
    """Test editing JSON in an editor."""
    # Setup
    json_data = [{"name": "Test", "value": {"tcp_port": 443}}]

    # Mock the temporary file
    mock_temp_file = MagicMock()
    mock_temp_file.name = "/tmp/test.json"
    mock_tempfile.return_value.__enter__.return_value = mock_temp_file

    # Mock the file read after editing
    mock_file_handle = MagicMock()
    mock_open.return_value.__enter__.return_value = mock_file_handle
    mock_file_handle.read.return_value = (
        '[{"name": "Test", "value": {"tcp_port": 8080}}]'
    )

    # Call the function
    result = edit_json_in_editor(json_data)

    # Assertions
    assert result == [{"name": "Test", "value": {"tcp_port": 8080}}]
    mock_subprocess.assert_called_once()
    mock_open.assert_called_once_with("/tmp/test.json", "r")
    mock_unlink.assert_called_once_with("/tmp/test.json")


@patch("ld_json_flag.interactive.os.unlink")
@patch("ld_json_flag.interactive.input")
@patch("ld_json_flag.interactive.select_project")
@patch("ld_json_flag.interactive.select_flag")
@patch("ld_json_flag.interactive.edit_json_in_editor")
def test_interactive_workflow_create_flag(
    mock_editor, mock_select_flag, mock_select_project, mock_input, mock_unlink
):
    """Test the interactive workflow for creating a flag."""
    # Setup
    client = MagicMock()
    client.project_key = None

    # Mock user selections
    mock_select_project.return_value = "test-project"
    mock_input.side_effect = [
        "1",
        "Test Flag",
        "",
        "y",
    ]  # Create flag, name, default key, confirm

    # Mock environments
    client.get_environments.return_value = [
        {"key": "production", "name": "Production"},
        {"key": "development", "name": "Development"},
    ]

    # Mock editor
    mock_editor.return_value = [
        {"name": "Production", "value": {"tcp_port": 443}},
        {"name": "Development", "value": {"tcp_port": 8080}},
    ]

    # Mock tempfile and create_flag_workflow
    with patch(
        "ld_json_flag.interactive.tempfile.NamedTemporaryFile"
    ) as mock_tempfile, patch(
        "ld_json_flag.interactive.create_flag_workflow"
    ) as mock_create_workflow:

        # Setup tempfile
        mock_temp_file = MagicMock()
        mock_temp_file.name = "/tmp/variations.json"
        mock_tempfile.return_value.__enter__.return_value = mock_temp_file

        # Setup create_flag_workflow
        mock_create_workflow.return_value = True

        # Call the function
        result = interactive_workflow(client)

    # Assertions
    assert result is True
    mock_select_project.assert_called_once_with(client)
    assert client.project_key == "test-project"
    client.get_environments.assert_called_once_with("test-project")
    mock_editor.assert_called_once()
    mock_create_workflow.assert_called_once()
    mock_unlink.assert_called_once_with("/tmp/variations.json")


@patch("ld_json_flag.interactive.input")
@patch("ld_json_flag.interactive.select_project")
@patch("ld_json_flag.interactive.select_flag")
@patch("ld_json_flag.interactive.update_flag_variations_workflow")
def test_interactive_workflow_update_flag(
    mock_update_workflow, mock_select_flag, mock_select_project, mock_input
):
    """Test the interactive workflow for updating a flag."""
    # Setup
    client = MagicMock()
    client.project_key = None

    # Mock user selections
    mock_select_project.return_value = "test-project"
    mock_input.return_value = "2"  # Update flag

    # Mock update_flag_variations_workflow
    mock_update_workflow.return_value = True

    # Call the function
    result = interactive_workflow(client)

    # Assertions
    assert result is True
    mock_select_project.assert_called_once_with(client)
    assert client.project_key == "test-project"
    mock_update_workflow.assert_called_once_with(client, "test-project")


@patch("ld_json_flag.interactive.input")
@patch("ld_json_flag.interactive.select_project")
@patch("ld_json_flag.interactive.validate_flags_workflow")
def test_interactive_workflow_validate_flags(
    mock_validate_workflow, mock_select_project, mock_input
):
    """Test the interactive workflow for validating flags."""
    # Setup
    client = MagicMock()
    client.project_key = None

    # Mock user selections
    mock_select_project.return_value = "test-project"
    mock_input.side_effect = ["3", "y"]  # Validate flags, fix invalid

    # Mock validate_flags_workflow
    mock_validate_workflow.return_value = True

    # Call the function
    result = interactive_workflow(client)

    # Assertions
    assert result is True
    mock_select_project.assert_called_once_with(client)
    assert client.project_key == "test-project"
    mock_validate_workflow.assert_called_once_with(client, True, "test-project")


@patch("ld_json_flag.interactive.input")
@patch("ld_json_flag.interactive.select_project")
def test_interactive_workflow_quit(mock_select_project, mock_input):
    """Test quitting the interactive workflow."""
    # Setup
    client = MagicMock()
    client.project_key = None

    # Mock user selections
    mock_select_project.return_value = "test-project"
    mock_input.return_value = "q"  # Quit

    # Call the function
    result = interactive_workflow(client)

    # Assertions
    assert result is False
    mock_select_project.assert_called_once_with(client)
    assert client.project_key == "test-project"


@patch("ld_json_flag.interactive.input")
@patch("ld_json_flag.interactive.select_project")
def test_interactive_workflow_invalid_choice(mock_select_project, mock_input):
    """Test entering an invalid choice in the interactive workflow."""
    # Setup
    client = MagicMock()
    client.project_key = None

    # Mock user selections
    mock_select_project.return_value = "test-project"
    mock_input.side_effect = ["4", "q"]  # Invalid choice, then quit

    # Call the function
    result = interactive_workflow(client)

    # Assertions
    assert result is False
    mock_select_project.assert_called_once_with(client)
    assert client.project_key == "test-project"
