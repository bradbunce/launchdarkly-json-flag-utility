"""Interactive mode for LaunchDarkly JSON Flag Utility."""

import json
import tempfile
import subprocess
import os
import sys


def select_from_list(items, prompt, item_formatter=str):
    """
    Display a list of items and let the user select one.
    
    Args:
        items (list): List of items to select from
        prompt (str): Prompt to display
        item_formatter (callable): Function to format each item for display
        
    Returns:
        Any: The selected item or None if the list is empty
    """
    if not items:
        print("No items available.")
        return None
        
    print(prompt)
    for i, item in enumerate(items):
        print(f"{i+1}. {item_formatter(item)}")
        
    while True:
        try:
            choice = input("\nEnter number (or 'q' to quit): ")
            if choice.lower() == 'q':
                return None
                
            idx = int(choice) - 1
            if 0 <= idx < len(items):
                return items[idx]
            else:
                print(f"Please enter a number between 1 and {len(items)}")
        except ValueError:
            print("Please enter a valid number")


def select_project(client):
    """
    Let the user select a project.
    
    Args:
        client (LaunchDarklyClient): LaunchDarkly client
        
    Returns:
        str: Project key or None if cancelled
    """
    print("\nFetching projects...")
    projects = client.get_projects()
    
    selected = select_from_list(
        projects, 
        "\nAvailable projects:", 
        lambda p: f"{p['name']} (key: {p['key']})"
    )
    
    return selected['key'] if selected else None


def select_flag(client, project_key):
    """
    Let the user select a feature flag.
    
    Args:
        client (LaunchDarklyClient): LaunchDarkly client
        project_key (str): LaunchDarkly project key
        
    Returns:
        str: Flag key or None if cancelled
    """
    print(f"\nFetching feature flags for project '{project_key}'...")
    flags = client.get_feature_flags(project_key)
    
    # Filter to flags that have JSON values
    json_flags = []
    for flag in flags:
        # Get the flag details to check its variations
        try:
            flag_details = client.get_feature_flag(flag.get('key'), project_key)
            variations = flag_details.get('variations', [])
            
            # Check if any variation has a JSON value (dictionary)
            for variation in variations:
                value = variation.get('value')
                if isinstance(value, dict):
                    json_flags.append(flag)
                    break
        except Exception as e:
            print(f"Error checking flag {flag.get('key')}: {str(e)}")
    
    if not json_flags:
        print(f"No JSON feature flags found in project '{project_key}'.")
        return None
    
    selected = select_from_list(
        json_flags,
        "\nAvailable JSON feature flags:",
        lambda f: f"{f['name']} (key: {f['key']})"
    )
    
    return selected['key'] if selected else None


def edit_json_in_editor(json_data):
    """
    Open JSON data in the user's preferred editor.
    
    Args:
        json_data: JSON serializable data
        
    Returns:
        dict: Edited JSON data or None if editing was cancelled
    """
    # Display instructions in the terminal
    print("\nINSTRUCTIONS:")
    print("1. Edit the JSON data to define your feature flag variations")
    print("2. Each variation needs a name, description, and value")
    print("3. The value must contain a tcp_port property with a valid port number (0-65535)")
    print("4. To add a new variation, add a new JSON object to the array")
    print("5. To remove a variation, delete its JSON object from the array")
    print("6. When adding a new variation, you can omit the _id field - it will be generated automatically")
    print("7. Save the file and close the editor when you're done")
    print("\nExample structure:")
    print("""[
  {
    "name": "Production",
    "description": "Production configuration",
    "value": {"tcp_port": 443}
  },
  {
    "name": "Development",
    "description": "Development configuration",
    "value": {"tcp_port": 8080}
  },
  {
    "name": "Staging",
    "description": "Staging configuration",
    "value": {"tcp_port": 8443}
  }
]""")
    print("\nOpening editor now...")
    
    # Determine the editor to use
    editor = os.environ.get('EDITOR', 'vim')
    if os.name == 'nt':  # Windows
        editor = os.environ.get('EDITOR', 'notepad')
    
    # Create a temporary file with just the JSON data (no comments)
    with tempfile.NamedTemporaryFile(suffix='.json', mode='w+', delete=False) as temp_file:
        # Write the JSON data to the file with proper formatting
        temp_file.write(json.dumps(json_data, indent=2))
        temp_file_path = temp_file.name
    
    try:
        # Open the editor
        subprocess.call([editor, temp_file_path])
        
        # Read the modified content
        with open(temp_file_path, 'r') as temp_file:
            try:
                return json.load(temp_file)
            except json.JSONDecodeError as e:
                print(f"❌ Error: Invalid JSON format: {str(e)}")
                return None
    finally:
        # Clean up the temporary file
        os.unlink(temp_file_path)


def update_flag_variations_workflow(client, project_key=None):
    """
    Interactive workflow for updating feature flag variations.
    
    Args:
        client (LaunchDarklyClient): LaunchDarkly client
        project_key (str, optional): LaunchDarkly project key
        
    Returns:
        bool: True if successful, False otherwise
    """
    # Select project if not provided
    if not project_key:
        project_key = select_project(client)
        if not project_key:
            return False
    
    # Update the client's project_key
    client.project_key = project_key
    
    # Select feature flag
    flag_key = select_flag(client, project_key)
    if not flag_key:
        return False
    
    # Get flag details
    try:
        flag = client.get_feature_flag(flag_key, project_key)
    except Exception as e:
        print(f"❌ Error retrieving flag details: {str(e)}")
        return False
    
    # Extract variations
    variations = flag.get('variations', [])
    if not variations:
        print(f"❌ No variations found for flag '{flag_key}'.")
        return False
    
    print("\nCurrent variations:")
    for i, var in enumerate(variations):
        print(f"{i+1}. {var.get('name')}: {json.dumps(var.get('value'))}")
    
    # Let the user edit the variations
    print("\nOpening editor to modify flag variations...")
    print("You can edit, add, or remove variations. Please follow the instructions below.")
    edited_variations = edit_json_in_editor(variations)
    
    if not edited_variations:
        print("❌ Editing cancelled or invalid JSON.")
        return False
    
    # Confirm the update
    print("\nUpdated variations:")
    for i, var in enumerate(edited_variations):
        print(f"{i+1}. {var.get('name')}: {json.dumps(var.get('value'))}")
    
    confirm = input("\nUpdate the flag with these variations? (y/n): ")
    if confirm.lower() != 'y':
        print("Update cancelled.")
        return False
    
    # Validate and update the variations
    try:
        client.update_flag_variations(flag_key, edited_variations, project_key)
        print(f"✅ Successfully updated variations for flag '{flag_key}'")
        return True
    except Exception as e:
        print(f"❌ Error updating flag variations: {str(e)}")
        return False


def create_flag_workflow(client, flag_key, flag_name, variations_file, env_rules=None, project_key=None):
    """
    Create a new feature flag with JSON variations.
    
    Args:
        client (LaunchDarklyClient): LaunchDarkly client
        flag_key (str): Feature flag key
        flag_name (str): Feature flag name
        variations_file (str): Path to JSON file with variations
        env_rules (list, optional): List of environment:rules_file pairs
        project_key (str, optional): Project key (if not already set in client)
        
    Returns:
        bool: True if successful, False otherwise
    """
    # If project_key is not provided and not set in client, prompt for selection
    if not project_key and not client.project_key:
        project_key = select_project(client)
        if not project_key:
            return False
        client.project_key = project_key
    
    # Load variations from JSON file
    try:
        with open(variations_file, 'r') as f:
            variations = json.load(f)
    except Exception as e:
        print(f"❌ Error loading variations from file: {str(e)}")
        return False
    
    # Create the feature flag
    try:
        result = client.create_feature_flag(
            flag_key, 
            flag_name, 
            variations,
            project_key
        )
    except Exception as e:
        print(f"❌ Error creating feature flag: {str(e)}")
        return False
    
    # Process environment targeting rules if provided
    if env_rules:
        for env_rule in env_rules:
            try:
                env, rule_path = env_rule.split(':', 1)
                
                with open(rule_path, 'r') as f:
                    targeting_rules = json.load(f)
                    
                client.configure_environment_targeting(
                    flag_key, 
                    env, 
                    targeting_rules,
                    project_key
                )
            except ValueError:
                print(f"❌ Invalid format for environment rules: {env_rule}")
                print("Format should be 'environment:path.json'")
            except Exception as e:
                print(f"❌ Error configuring environment '{env}': {str(e)}")
    
    print("✅ Feature flag setup complete")
    return True


def interactive_workflow(client):
    """
    Main interactive workflow that asks the user if they want to create or update a flag.
    
    Args:
        client (LaunchDarklyClient): LaunchDarkly client
        
    Returns:
        bool: True if successful, False otherwise
    """
    # Select project
    project_key = select_project(client)
    if not project_key:
        return False
    
    # Update the client's project_key
    client.project_key = project_key
    
    # Ask if the user wants to create or update a flag
    print("\nWhat would you like to do?")
    print("1. Create a new JSON feature flag")
    print("2. Update an existing JSON feature flag")
    
    while True:
        choice = input("\nEnter number (or 'q' to quit): ")
        if choice.lower() == 'q':
            return False
            
        if choice == '1':
            # Create a new flag - ask for name first
            flag_name = input("\nEnter feature flag name: ")
            if not flag_name:
                print("Flag name cannot be empty.")
                continue
            
            # Auto-generate a key from the name and allow user to change it
            suggested_key = flag_name.lower().replace(' ', '-')
            flag_key = input(f"Enter feature flag key (suggested: {suggested_key}): ") or suggested_key
            if not flag_key:
                print("Flag key cannot be empty.")
                continue
            
            # Get environments for the selected project
            try:
                print("\nFetching environments for the selected project...")
                environments = client.get_environments(project_key)
                
                # Create template variations based on project environments
                template_variations = []
                
                # If no environments found, use default template
                if not environments:
                    print("No environments found. Using default template.")
                    template_variations = [
                        {
                            "name": "Production",
                            "description": "Production configuration",
                            "value": {"tcp_port": 443}
                        },
                        {
                            "name": "Development",
                            "description": "Development configuration",
                            "value": {"tcp_port": 8080}
                        }
                    ]
                else:
                    # Create a variation for each environment
                    for i, env in enumerate(environments):
                        env_name = env.get("name", f"Environment {i+1}")
                        env_key = env.get("key", f"env-{i+1}")
                        
                        # Use different port numbers for different environments
                        port = 443 if "prod" in env_key.lower() else 8080
                        
                        template_variations.append({
                            "name": env_name,
                            "description": f"{env_name} configuration",
                            "value": {"tcp_port": port}
                        })
                    
                    print(f"Created template with {len(template_variations)} variations based on project environments.")
            except Exception as e:
                print(f"Error fetching environments: {str(e)}. Using default template.")
                template_variations = [
                    {
                        "name": "Production",
                        "description": "Production configuration",
                        "value": {"tcp_port": 443}
                    },
                    {
                        "name": "Development",
                        "description": "Development configuration",
                        "value": {"tcp_port": 8080}
                    }
                ]
            
            print("\nOpening editor to define your flag variations...")
            print("You can edit, add, or remove variations. Please follow the instructions below.")
            variations = edit_json_in_editor(template_variations)
            
            if not variations:
                print("❌ Editing cancelled or invalid JSON.")
                return False
            
            # Save variations to a temporary file
            with tempfile.NamedTemporaryFile(suffix='.json', mode='w+', delete=False) as temp_file:
                json.dump(variations, temp_file, indent=2)
                variations_file = temp_file.name
            
            try:
                # Create the flag without targeting rules
                return create_flag_workflow(client, flag_key, flag_name, variations_file, None, project_key)
            finally:
                # Clean up temporary files
                os.unlink(variations_file)
            
        elif choice == '2':
            # Update an existing flag, passing the already selected project_key
            return update_flag_variations_workflow(client, project_key)
        else:
            print("Please enter 1 or 2")
