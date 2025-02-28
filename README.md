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
git clone https://github.com/yourusername/launchdarkly-json-flag-utility.git
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

### Creating a New Feature Flag

```bash
python -m ld_json_flag.cli create \
  --api-key "api-12345" \
  --project-key "my-project" \
  --flag-key "tcp-port-config" \
  --flag-name "TCP Port Configuration" \
  --variations examples/variations.json
```

### Updating an Existing Flag (Interactive Mode)

```bash
python -m ld_json_flag.cli update \
  --api-key "api-12345"
```

This will:

1. Prompt you to select a project
2. Display all JSON feature flags in that project
3. Allow you to select a flag to update
4. Open the current variations in your default editor
5. Allow you to edit, add, or remove variations:
   - To add a variation: Add a new JSON object to the array
   - To remove a variation: Delete its JSON object from the array
   - To edit a variation: Modify the existing JSON object
   - When adding a new variation, you can omit the \_id field
6. Validate the edited variations
7. Update the flag with the new variations

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
