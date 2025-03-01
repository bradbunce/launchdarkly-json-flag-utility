#!/usr/bin/env python3
"""Command-line interface for LaunchDarkly JSON Flag Utility."""

import os
import sys
import argparse
from dotenv import load_dotenv

from ld_json_flag.client import LaunchDarklyClient
from ld_json_flag.interactive import (
    update_flag_variations_workflow,
    create_flag_workflow,
    interactive_workflow,
    validate_flags_workflow,
)


def parse_arguments():
    """
    Parse command line arguments.

    Returns:
        argparse.Namespace: Parsed arguments
    """
    desc = "Create and update LaunchDarkly feature flags with JSON variations"
    parser = argparse.ArgumentParser(description=desc)

    # Common arguments
    api_key_help = "LaunchDarkly API key (can also be set via LD_API_KEY env var)"
    parser.add_argument("--api-key", help=api_key_help)

    proj_key_help = (
        "LaunchDarkly project key (can also be set via LD_PROJECT_KEY env var)"
    )
    parser.add_argument("--project-key", help=proj_key_help)

    # Create subparsers for different commands
    subparsers = parser.add_subparsers(dest="command", help="Command to execute")

    # Validate command
    validate_parser = subparsers.add_parser(
        "validate", help="Validate existing JSON feature flags"
    )
    validate_parser.add_argument(
        "--fix", action="store_true", help="Prompt to fix invalid flags"
    )

    # Create command
    create_parser = subparsers.add_parser("create", help="Create a new feature flag")
    create_parser.add_argument("--flag-key", required=True, help="Feature flag key")
    create_parser.add_argument("--flag-name", required=True, help="Feature flag name")
    create_parser.add_argument(
        "--variations", required=True, help="JSON file path containing variations"
    )

    # Update command
    # We don't use the variable but need to create the subparser
    subparsers.add_parser("update", help="Update an existing feature flag")

    # For backward compatibility, allow running without a command
    flag_key_help = "Feature flag key (for create mode)"
    parser.add_argument("--flag-key", dest="create_flag_key", help=flag_key_help)

    flag_name_help = "Feature flag name (for create mode)"
    parser.add_argument("--flag-name", dest="create_flag_name", help=flag_name_help)

    variations_help = "JSON file path containing variations (for create mode)"
    parser.add_argument("--variations", dest="create_variations", help=variations_help)

    env_rules_help = (
        "JSON file path(s) for environment targeting rules (for create mode)"
    )
    parser.add_argument(
        "--env-rules", dest="create_env_rules", nargs="+", help=env_rules_help
    )

    return parser.parse_args()


def main():
    """
    Main function to run the script.

    Returns:
        int: Exit code (0 for success, non-zero for failure)
    """
    # Load environment variables from .env file if it exists
    load_dotenv()

    args = parse_arguments()

    # Get API key from args or environment
    api_key = args.api_key or os.environ.get("LD_API_KEY")
    if not api_key:
        error_msg = (
            "❌ Error: API key is required. "
            "Provide it via --api-key or LD_API_KEY env var."
        )
        print(error_msg)
        return 1

    # Get project key from args or environment
    project_key = args.project_key or os.environ.get("LD_PROJECT_KEY")

    # Initialize the LaunchDarkly client
    client = LaunchDarklyClient(api_key, project_key)

    # Determine the command to execute
    if args.command == "validate":
        # Run the validate workflow
        success = validate_flags_workflow(client, args.fix, project_key)
        return 0 if success else 1
    elif args.command == "update":
        # Run the update workflow
        success = update_flag_variations_workflow(client)
        return 0 if success else 1
    elif args.command == "create":
        # Run the create workflow with the args from the create command
        success = create_flag_workflow(
            client,
            args.flag_key,
            args.flag_name,
            args.variations,
            None,  # No environment rules
            project_key,
        )
        return 0 if success else 1
    elif args.create_flag_key and args.create_flag_name and args.create_variations:
        # Backward compatibility: run create workflow with the legacy args
        success = create_flag_workflow(
            client,
            args.create_flag_key,
            args.create_flag_name,
            args.create_variations,
            None,  # No environment rules
            project_key,
        )
        return 0 if success else 1
    else:
        # Default to interactive workflow if no specific args provided
        print("No command specified. Running in interactive mode...\n")
        success = interactive_workflow(client)
        return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
