# LaunchDarkly JSON Flag Utility

A CLI and web application to create, update, and validate LaunchDarkly feature flags with JSON variations. Includes AI-powered fix suggestions via LaunchDarkly AI Configs and Amazon Bedrock.

## Features

- Create new feature flags with JSON variations at the project level
- Add, edit, or remove variations from JSON feature flags
- Validate existing JSON feature flags against schema requirements
- Automatically fix invalid flag variations through interactive editing (CLI) or AI suggestions (Web UI)
- Inline JSON editor in the web UI for direct variation editing
- AI-powered fix suggestions using LaunchDarkly AI Configs with Amazon Bedrock
- Web dashboard with project selector and real-time validation status
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

```bash
# Create a virtual environment
python3 -m venv .venv

# Activate the virtual environment
# On macOS/Linux:
source .venv/bin/activate
# On Windows:
# .venv\Scripts\activate
```

### For Regular Users

After activating your virtual environment, install the package:

```bash
pip install .
```

This will make the `ld-json-flag` (CLI) and `ld-json-flag-web` (web UI) commands available.

### For Developers

After activating your virtual environment, install the package in development mode:

```bash
pip install -e .
```

This creates an "editable" installation where changes to the source code are immediately reflected without needing to reinstall.

## Configuration

Copy the example environment file and fill in your values:

```bash
cp .env.example .env
```

### Required Environment Variables

| Variable | Description |
|----------|-------------|
| `LD_API_KEY` | LaunchDarkly API key (for flag management) |

### Required for Web UI AI Features

| Variable | Description |
|----------|-------------|
| `LD_SDK_KEY` | LaunchDarkly server-side SDK key (for AI Configs) |

### Optional Environment Variables

| Variable | Description |
|----------|-------------|
| `LD_PROJECT_KEY` | Default project key (web UI has a selector, CLI will prompt if not set) |
| `AWS_REGION` | AWS region override (defaults to AWS CLI profile region) |
| `AWS_ACCESS_KEY_ID` | AWS access key (if not using AWS CLI profile) |
| `AWS_SECRET_ACCESS_KEY` | AWS secret key (if not using AWS CLI profile) |
| `EDITOR` | Editor for interactive CLI editing (defaults to vim/notepad) |

For AWS credentials, the app supports both explicit keys in `.env` and the default AWS CLI profile (`aws configure`). If you have the AWS CLI configured, no AWS environment variables are needed.

## Web UI

The web interface provides a dashboard for viewing and managing JSON feature flags with AI-powered fix suggestions.

### Running the Web UI

```bash
ld-json-flag-web
```

Then open http://localhost:8080 in your browser.

### Features

- Project selector dropdown — switch between LaunchDarkly projects
- Dashboard showing all JSON flags with validation status (✅/❌)
- Inline JSON editor — edit variation values directly in the browser
- One-click validation refresh
- AI-powered fix suggestions for invalid variations using LaunchDarkly AI Configs
- One-click apply for AI-suggested fixes

### LaunchDarkly AI Configs Integration

The web UI uses LaunchDarkly AI Configs to manage the AI model and prompts for fix suggestions. This means you can change the model, adjust the prompt, or modify parameters directly in the LaunchDarkly UI without redeploying the app.

**Setup:**

1. Create a Completion-mode AI Config in LaunchDarkly named `json-validation-assistant`
2. Select an Amazon Bedrock model (e.g., Claude Haiku 4.5)
3. Set parameters: `temperature: 0`, `max_tokens: 256`
4. Add a system message defining the assistant's role and validation rules
5. Add a user message with template variables: `{{flag_name}}`, `{{flag_key}}`, `{{variation_name}}`, `{{variation_value}}`, `{{error_message}}`
6. Enable targeting and set the default rule to serve your variation

The app automatically prepends the `us.` inference profile prefix for Bedrock models.

## CLI Usage

### Interactive Mode

```bash
ld-json-flag
```

When run without arguments, the tool guides you through:

1. Selecting a project
2. Choosing an action (create, update, or validate)
3. For new flags: entering a name/key and defining variations in your editor
4. For existing flags: selecting and editing variations
5. For validation: reviewing results and optionally fixing invalid flags

### Command-Line Arguments

#### Create a new flag

```bash
ld-json-flag create --flag-key my-flag --flag-name "My Flag" --variations examples/variations.json
```

#### Update an existing flag

```bash
ld-json-flag update
```

#### Validate existing flags

```bash
ld-json-flag validate
```

To interactively fix invalid flags:

```bash
ld-json-flag validate --fix
```

#### Additional options

```bash
ld-json-flag --api-key your-api-key --project-key your-project-key create --flag-key my-flag --flag-name "My Flag" --variations examples/variations.json
```

For a complete list of arguments:

```bash
ld-json-flag --help
```

## JSON Schema Validation

The tool validates that all JSON variations follow the TCP port schema:

- Each variation must contain a `tcp_port` property
- The `tcp_port` value must be an integer
- The `tcp_port` value must be between 0 and 65535

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

```bash
pip install pytest
python3 -m pytest tests/
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
