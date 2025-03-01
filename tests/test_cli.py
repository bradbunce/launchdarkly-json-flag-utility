"""Tests for the CLI functionality."""

from unittest.mock import patch, MagicMock, ANY
import sys
from io import StringIO
from ld_json_flag.cli import main, parse_arguments


@patch("ld_json_flag.cli.validate_flags_workflow")
@patch("ld_json_flag.cli.LaunchDarklyClient")
@patch("sys.argv", ["ld_json_flag.cli", "--api-key", "fake-key", "validate"])
def test_validate_command(mock_client_class, mock_validate_workflow):
    """Test the validate command."""
    # Setup
    mock_client = MagicMock()
    mock_client_class.return_value = mock_client
    mock_validate_workflow.return_value = True

    # Call the function
    result = main()

    # Assertions
    mock_client_class.assert_called_once_with("fake-key", ANY)
    mock_validate_workflow.assert_called_once_with(mock_client, False, ANY)
    assert result == 0


@patch("ld_json_flag.cli.validate_flags_workflow")
@patch("ld_json_flag.cli.LaunchDarklyClient")
@patch("sys.argv", ["ld_json_flag.cli", "--api-key", "fake-key", "validate", "--fix"])
def test_validate_command_with_fix(mock_client_class, mock_validate_workflow):
    """Test the validate command with fix option."""
    # Setup
    mock_client = MagicMock()
    mock_client_class.return_value = mock_client
    mock_validate_workflow.return_value = True

    # Call the function
    result = main()

    # Assertions
    mock_client_class.assert_called_once_with("fake-key", ANY)
    mock_validate_workflow.assert_called_once_with(mock_client, True, ANY)
    assert result == 0


@patch("ld_json_flag.cli.update_flag_variations_workflow")
@patch("ld_json_flag.cli.LaunchDarklyClient")
@patch("sys.argv", ["ld_json_flag.cli", "--api-key", "fake-key", "update"])
def test_update_command(mock_client_class, mock_update_workflow):
    """Test the update command."""
    # Setup
    mock_client = MagicMock()
    mock_client_class.return_value = mock_client
    mock_update_workflow.return_value = True

    # Call the function
    result = main()

    # Assertions
    mock_client_class.assert_called_once_with("fake-key", ANY)
    mock_update_workflow.assert_called_once_with(mock_client)
    assert result == 0


@patch("ld_json_flag.cli.create_flag_workflow")
@patch("ld_json_flag.cli.LaunchDarklyClient")
@patch(
    "sys.argv",
    [
        "ld_json_flag.cli",
        "--api-key",
        "fake-key",
        "create",
        "--flag-key",
        "test-flag",
        "--flag-name",
        "Test Flag",
        "--variations",
        "variations.json",
    ],
)
def test_create_command(mock_client_class, mock_create_workflow):
    """Test the create command."""
    # Setup
    mock_client = MagicMock()
    mock_client_class.return_value = mock_client
    mock_create_workflow.return_value = True

    # Call the function
    result = main()

    # Assertions
    mock_client_class.assert_called_once_with("fake-key", ANY)
    mock_create_workflow.assert_called_once_with(
        mock_client, "test-flag", "Test Flag", "variations.json", None, ANY
    )
    assert result == 0


@patch("ld_json_flag.cli.interactive_workflow")
@patch("ld_json_flag.cli.LaunchDarklyClient")
@patch("sys.argv", ["ld_json_flag.cli", "--api-key", "fake-key"])
def test_interactive_mode(mock_client_class, mock_interactive_workflow):
    """Test the interactive mode."""
    # Setup
    mock_client = MagicMock()
    mock_client_class.return_value = mock_client
    mock_interactive_workflow.return_value = True

    # Capture stdout
    captured_output = StringIO()
    sys.stdout = captured_output

    try:
        # Call the function
        result = main()

        # Assertions
        mock_client_class.assert_called_once_with("fake-key", ANY)
        mock_interactive_workflow.assert_called_once_with(mock_client)
        assert result == 0
        assert (
            "No command specified. Running in interactive mode..."
            in captured_output.getvalue()
        )
    finally:
        sys.stdout = sys.__stdout__


@patch("ld_json_flag.cli.os.environ.get")
def test_api_key_from_env(mock_environ_get):
    """Test getting API key from environment variable."""
    # Setup
    mock_environ_get.side_effect = lambda key, default=None: (
        "env-api-key" if key == "LD_API_KEY" else default
    )

    # Call the function with no API key in args
    with patch("sys.argv", ["ld_json_flag.cli"]):
        args = parse_arguments()

    # Mock the main function to avoid actually running it
    with patch("ld_json_flag.cli.LaunchDarklyClient"), patch(
        "ld_json_flag.cli.interactive_workflow"
    ):
        with patch("sys.argv", ["ld_json_flag.cli"]):
            main()

    # Assertions
    assert args.api_key is None  # Args don't have API key
    mock_environ_get.assert_any_call("LD_API_KEY")  # But env var is checked


@patch("ld_json_flag.cli.os.environ.get")
def test_project_key_from_env(mock_environ_get):
    """Test getting project key from environment variable."""
    # Setup
    mock_environ_get.side_effect = lambda key, default=None: {
        "LD_API_KEY": "env-api-key",
        "LD_PROJECT_KEY": "env-project-key",
    }.get(key, default)

    # Call the function with no project key in args
    with patch("sys.argv", ["ld_json_flag.cli", "--api-key", "arg-api-key"]):
        args = parse_arguments()

    # Mock the main function to avoid actually running it
    with patch("ld_json_flag.cli.LaunchDarklyClient"), patch(
        "ld_json_flag.cli.interactive_workflow"
    ):
        with patch("sys.argv", ["ld_json_flag.cli", "--api-key", "arg-api-key"]):
            main()

    # Assertions
    assert args.project_key is None  # Args don't have project key
    mock_environ_get.assert_any_call("LD_PROJECT_KEY")  # But env var is checked


@patch("ld_json_flag.cli.load_dotenv")
def test_load_dotenv_called(mock_load_dotenv):
    """Test that load_dotenv is called."""
    # Mock the main function to avoid actually running it
    with patch("ld_json_flag.cli.LaunchDarklyClient"), patch(
        "ld_json_flag.cli.interactive_workflow"
    ), patch("ld_json_flag.cli.os.environ.get", return_value="fake-key"), patch(
        "sys.argv", ["ld_json_flag.cli"]
    ):
        main()

    # Assertions
    mock_load_dotenv.assert_called_once()


@patch("sys.stdout", new_callable=StringIO)
def test_missing_api_key(mock_stdout):
    """Test error when API key is missing."""
    # Mock environment and arguments to ensure no API key is available
    with patch("ld_json_flag.cli.os.environ.get", return_value=None), patch(
        "sys.argv", ["ld_json_flag.cli"]
    ):
        result = main()

    # Assertions
    assert result == 1  # Should return error code
    assert "Error: API key is required" in mock_stdout.getvalue()
