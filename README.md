# LaunchDarkly JSON Flag Utility

A command-line tool to create and update LaunchDarkly feature flags with JSON variations.

## Features

- Create new feature flags with JSON variations at the project level
- Update variations of existing JSON feature flags
- Add, edit, or remove variations from JSON feature flags
- JSON schema validation for TCP port configuration
- Interactive mode for selecting projects and flags
- Command-line interface for easy integration with CI/CD pipelines

## Installation

Clone this repository:

```bash
git clone https://github.com/bradbunce/launchdarkly-json-flag-utility.git
cd launchdarkly-json-flag-utility
```

Install dependencies:

```bash
pip install -r requirements.txt
```

For development:

```bash
pip install -e .
```

## Usage

The simplest way to use the utility is in interactive mode:

```bash
python -m ld_json_flag.cli
```

This will guide you through the process of:

1. Selecting a project
2. Choosing to create a new flag or update an existing one
3. For new flags:
   - Entering a name and key
   - Defining variations in your default editor
4. For existing flags:
   - Selecting a flag from the project
   - Editing variations in your default editor
5. Validating and saving your changes

When editing variations, you can:

- Add a variation by adding a new JSON object to the array
- Remove a variation by deleting its JSON object
- Edit a variation by modifying the existing JSON object
- When adding a new variation, you can omit the \_id field

Advanced usage with command-line arguments is also available. See `python -m ld_json_flag.cli --help` for details.

## JSON Schema Validation

The tool validates that all JSON variations follow the TCP port schema:

- Each variation must contain a `tcp_port` property
- The `tcp_port` value must be an integer
- The `tcp_port` value must be between 0 and 65535

## Environment Variables

You can set the following environment variables instead of using command-line arguments:

- `LD_API_KEY`: Your LaunchDarkly API key
- `LD_PROJECT_KEY`: Your default LaunchDarkly project key
- `EDITOR`: The editor to use for interactive editing (defaults to vim on Linux/Mac, notepad on Windows)

You can also create a `.env` file in the project directory:

```
LD_API_KEY=api-12345
LD_PROJECT_KEY=default
```

## Example JSON Files

### Variations (examples/variations.json)

```json
[
  {
    "name": "Production Port",
    "description": "Standard production port",
    "value": { "tcp_port": 443 }
  },
  {
    "name": "Development Port",
    "description": "Alternative development port",
    "value": { "tcp_port": 8080 }
  },
  {
    "name": "Testing Port",
    "description": "Testing environment port",
    "value": { "tcp_port": 9000 }
  }
]
```

## Testing

The project includes comprehensive tests for all functionality. To run the tests:

```bash
python -m pytest tests/
```

The test suite covers:

- TCP port JSON validation
- API interactions with LaunchDarkly (mocked)
- Creating and updating feature flags
- Getting projects, environments, and flags

## VS Code Integration

This repo includes VS Code configuration for:

- Debugging and running the script
- Code formatting with Black
- Linting with Pylint and Flake8
- Running tests with pytest

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the LICENSE file for details.
