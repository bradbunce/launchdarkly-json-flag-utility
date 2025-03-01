# LaunchDarkly JSON Flag Utility

A command-line tool to create and update LaunchDarkly feature flags with JSON variations.

## Features

- Create new feature flags with JSON variations at the project level
- Add, edit, or remove variations from JSON feature flags
- Validate existing JSON feature flags against schema requirements
- Automatically fix invalid flag variations through interactive editing
- Example JSON schema validation for TCP port configuration
- Interactive mode for selecting projects and flags
- Command-line interface for easy integration with CI/CD pipelines

## Installation

Clone this repository:

```bash
git clone https://github.com/bradbunce/launchdarkly-json-flag-utility.git
cd launchdarkly-json-flag-utility
```

### Using a Virtual Environment (Recommended)

It's recommended to use a virtual environment to avoid conflicts with system packages:

```bash
# Create a virtual environment
python -m venv venv

# Activate the virtual environment
# On macOS/Linux:
source venv/bin/activate
# On Windows:
# venv\Scripts\activate
```

### For Regular Users

After activating your virtual environment, install the package:

```bash
pip install .
```

This will make the `ld-json-flag` command available in your environment.

### For Developers

After activating your virtual environment, install the package in development mode:

```bash
pip install -e .
```

This creates an "editable" installation where changes to the source code are immediately reflected without needing to reinstall.

### Quick Start Without Installation

If you just want to try the utility without installing it, you can install only the dependencies and run it directly:

```bash
# Install dependencies
pip install -r requirements.txt

# Run the utility
python -m ld_json_flag.cli
```

## Usage

### Interactive Mode

The simplest way to use the utility is in interactive mode:

```bash
python -m ld_json_flag.cli
```

When run without any arguments, you'll see the message "No command specified. Running in interactive mode..." and the tool will guide you through the process interactively:

1. Selecting a project
2. Choosing what you want to do:
   - Create a new JSON feature flag
   - Update an existing JSON feature flag
   - Validate existing JSON feature flags
3. For new flags:
   - Entering a name and key
   - Defining variations in your default editor
4. For existing flags:
   - Selecting a flag from the project
   - Editing variations in your default editor
5. For validation:
   - Choosing whether to fix invalid flags if found
   - Reviewing validation results
   - Optionally editing and fixing invalid flags
6. Validating and saving your changes

When editing variations, you can:

- Add a variation by adding a new JSON object to the array
- Remove a variation by deleting its JSON object
- Edit a variation by modifying the existing JSON object
- When adding a new variation, you can omit the \_id field

### Command-Line Arguments

For automation or CI/CD pipelines, you can use specific commands with arguments:

#### Create a new flag

```bash
python -m ld_json_flag.cli create --flag-key my-flag --flag-name "My Flag" --variations examples/variations.json
```

#### Update an existing flag

```bash
python -m ld_json_flag.cli update
```

This will still prompt you to select a project and flag, but will skip the initial mode selection.

#### Validate existing flags

```bash
python -m ld_json_flag.cli validate
```

This powerful feature scans all JSON feature flags in a project and validates them against the TCP port schema requirements. The validation process:

1. Automatically discovers all JSON feature flags in the selected project
2. Checks each variation in each flag for schema compliance
3. Provides detailed reports of any validation errors found
4. Summarizes the validation results

If invalid flags are found, the tool will report them but not modify them by default.

To automatically prompt for fixing invalid flags:

```bash
python -m ld_json_flag.cli validate --fix
```

With the `--fix` option, the utility will:

1. Open your editor to fix each invalid flag's variations
2. Re-validate the changes before applying them
3. Only update flags that have been successfully fixed
4. Skip flags that still have validation errors after editing

This feature is particularly valuable for maintaining consistency across feature flags, especially in projects with many flags or multiple contributors.

#### Additional options

You can specify the API key and project key as arguments:

```bash
python -m ld_json_flag.cli --api-key your-api-key --project-key your-project-key create --flag-key my-flag --flag-name "My Flag" --variations examples/variations.json
```

For a complete list of available arguments, run:

```bash
python -m ld_json_flag.cli --help
```

## Example JSON Schema Validation

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
