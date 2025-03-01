"""Client for interacting with LaunchDarkly API."""

import json
import requests


class LaunchDarklyClient:
    """Client for interacting with LaunchDarkly API to create and configure feature flags."""

    def __init__(self, api_key, project_key=None):
        """
        Initialize LaunchDarkly client.

        Args:
            api_key (str): LaunchDarkly API key
            project_key (str, optional): LaunchDarkly project key
        """
        self.api_key = api_key
        self.project_key = project_key
        self.base_url = "https://app.launchdarkly.com/api/v2"
        self.headers = {"Authorization": api_key, "Content-Type": "application/json"}

    def validate_tcp_port_json(self, json_obj):
        """
        Validate that a JSON object conforms to the TCP port schema.

        Schema requirement: tcp_port: integer value between 0 and 65535

        Args:
            json_obj (dict): JSON object to validate

        Returns:
            bool: True if validation passes

        Raises:
            ValueError: If validation fails
        """
        # Check if it's an object
        if not isinstance(json_obj, dict):
            raise ValueError("JSON must be an object")

        # Check if it has tcp_port property
        if "tcp_port" not in json_obj:
            raise ValueError("JSON must contain a tcp_port property")

        # Validate tcp_port value
        port_value = json_obj["tcp_port"]

        if not isinstance(port_value, int):
            raise ValueError("tcp_port must be an integer")

        if port_value < 0 or port_value > 65535:
            raise ValueError("tcp_port must be between 0 and 65535")

        return True

    def get_projects(self):
        """
        Get list of all projects.

        Returns:
            list: List of project objects

        Raises:
            requests.exceptions.RequestException: If API request fails
        """
        all_items = []
        url = f"{self.base_url}/projects"

        # Handle pagination by following the 'next' link if it exists
        while url:
            response = requests.get(url, headers=self.headers)

            if response.status_code >= 400:
                print(f"❌ Error getting projects: {response.status_code}")
                print(f"Response: {response.text}")
                response.raise_for_status()

            data = response.json()
            all_items.extend(data.get("items", []))

            # Check if there's a next page
            url = None
            links = data.get("_links", {})
            if links and "next" in links and links["next"]:
                url = links["next"].get("href")

        return all_items

    def get_environments(self, project_key=None):
        """
        Get list of all environments for a project.

        Args:
            project_key (str, optional): LaunchDarkly project key (defaults to client's project_key)

        Returns:
            list: List of environment objects

        Raises:
            ValueError: If no project_key is provided
            requests.exceptions.RequestException: If API request fails
        """
        project_key = project_key or self.project_key
        if not project_key:
            raise ValueError("Project key is required to list environments")

        response = requests.get(
            f"{self.base_url}/projects/{project_key}", headers=self.headers
        )

        if response.status_code >= 400:
            print(f"❌ Error getting project details: {response.status_code}")
            print(f"Response: {response.text}")
            response.raise_for_status()

        # Extract environments from project details
        environments = response.json().get("environments", [])
        return environments

    def get_feature_flags(self, project_key=None):
        """
        Get list of all feature flags for a project.

        Args:
            project_key (str, optional): LaunchDarkly project key (defaults to client's project_key)

        Returns:
            list: List of feature flag objects

        Raises:
            ValueError: If no project_key is provided
            requests.exceptions.RequestException: If API request fails
        """
        project_key = project_key or self.project_key
        if not project_key:
            raise ValueError("Project key is required to list feature flags")

        all_items = []
        url = f"{self.base_url}/flags/{project_key}"

        # Handle pagination by following the 'next' link if it exists
        while url:
            response = requests.get(url, headers=self.headers)

            if response.status_code >= 400:
                print(f"❌ Error getting feature flags: {response.status_code}")
                print(f"Response: {response.text}")
                response.raise_for_status()

            data = response.json()
            all_items.extend(data.get("items", []))

            # Check if there's a next page
            url = None
            links = data.get("_links", {})
            if links and "next" in links and links["next"]:
                url = links["next"].get("href")

        return all_items

    def get_feature_flag(self, flag_key, project_key=None):
        """
        Get details of a specific feature flag.

        Args:
            flag_key (str): Feature flag key
            project_key (str, optional): LaunchDarkly project key (defaults to client's project_key)

        Returns:
            dict: Feature flag object

        Raises:
            ValueError: If no project_key is provided
            requests.exceptions.RequestException: If API request fails
        """
        project_key = project_key or self.project_key
        if not project_key:
            raise ValueError("Project key is required to get a feature flag")

        response = requests.get(
            f"{self.base_url}/flags/{project_key}/{flag_key}", headers=self.headers
        )

        if response.status_code >= 400:
            print(f"❌ Error getting feature flag details: {response.status_code}")
            print(f"Response: {response.text}")
            response.raise_for_status()

        return response.json()

    def create_feature_flag(self, flag_key, flag_name, variations, project_key=None):
        """
        Create a feature flag at the project level with JSON variations.

        Args:
            flag_key (str): Unique key for the feature flag
            flag_name (str): Display name for the feature flag
            variations (list): List of variation objects
            project_key (str, optional): LaunchDarkly project key (defaults to client's project_key)

        Returns:
            dict: API response data

        Raises:
            ValueError: If validation fails or no project_key is provided
            requests.exceptions.RequestException: If API request fails
        """
        project_key = project_key or self.project_key
        if not project_key:
            raise ValueError("Project key is required to create a feature flag")

        # Validate all variations first
        for i, variation in enumerate(variations):
            try:
                self.validate_tcp_port_json(variation["value"])
                print(f"✅ Variation {i + 1} is valid")
            except ValueError as e:
                raise ValueError(f"Validation failed for variation {i + 1}: {str(e)}")

        # Prepare the request payload for project-level flag creation
        payload = {
            "name": flag_name,
            "key": flag_key,
            "kind": "json",
            "variations": variations,
            "temporary": False,
            "tags": ["tcp", "network-config"],
            "defaults": {"onVariation": 0, "offVariation": 1},
        }

        print("Creating feature flag with the following configuration:")
        print(json.dumps(payload, indent=2))

        # Make API request to LaunchDarkly to create project-level flag
        response = requests.post(
            f"{self.base_url}/flags/{project_key}", headers=self.headers, json=payload
        )

        if response.status_code >= 400:
            print(f"❌ Error creating feature flag: {response.status_code}")
            print(f"Response: {response.text}")
            response.raise_for_status()

        print(f"✅ Feature flag '{flag_name}' created successfully at project level")
        print(f"Flag key: {flag_key}")
        print(f"API Response Status: {response.status_code}")
        return response.json()

    def update_flag_variations(self, flag_key, variations, project_key=None):
        """
        Update the variations of an existing feature flag.

        Args:
            flag_key (str): Feature flag key
            variations (list): List of variation objects
            project_key (str, optional): LaunchDarkly project key (defaults to client's project_key)

        Returns:
            dict: API response data

        Raises:
            ValueError: If validation fails or no project_key is provided
            requests.exceptions.RequestException: If API request fails
        """
        project_key = project_key or self.project_key
        if not project_key:
            raise ValueError("Project key is required to update a feature flag")

        # Validate all variations first
        for i, variation in enumerate(variations):
            try:
                self.validate_tcp_port_json(variation["value"])
                print(f"✅ Variation {i + 1} is valid")
            except ValueError as e:
                raise ValueError(f"Validation failed for variation {i + 1}: {str(e)}")

        # Prepare the patch instructions
        patch_payload = {
            "comment": "Updated flag variations via LD JSON Flag Utility",
            "patch": [{"op": "replace", "path": "/variations", "value": variations}],
        }

        print("Updating feature flag variations with:")
        print(json.dumps(variations, indent=2))

        # Make API request to LaunchDarkly to update the flag
        response = requests.patch(
            f"{self.base_url}/flags/{project_key}/{flag_key}",
            headers=self.headers,
            json=patch_payload,
        )

        if response.status_code >= 400:
            print(f"❌ Error updating feature flag variations: {response.status_code}")
            print(f"Response: {response.text}")
            response.raise_for_status()

        print(f"✅ Feature flag '{flag_key}' variations updated successfully")
        print(f"API Response Status: {response.status_code}")
        return response.json()

    def configure_environment_targeting(
        self, flag_key, environment_key, targeting_rules, project_key=None
    ):
        """
        Configure environment-specific targeting rules for a feature flag.

        Args:
            flag_key (str): Feature flag key
            environment_key (str): Environment key (e.g., 'production', 'development')
            targeting_rules (list): List of targeting rule objects
            project_key (str, optional): LaunchDarkly project key (defaults to client's project_key)

        Returns:
            dict: API response data

        Raises:
            ValueError: If no project_key is provided
            requests.exceptions.RequestException: If API request fails
        """
        project_key = project_key or self.project_key
        if not project_key:
            raise ValueError("Project key is required to configure targeting rules")

        print(f"Configuring targeting rules for environment: {environment_key}")

        # Prepare the patch for targeting rules
        patch_payload = {
            "instructions": [{"kind": "replaceRule", "rules": targeting_rules}]
        }

        # Update the environment-specific targeting rules
        response = requests.patch(
            f"{self.base_url}/flags/{project_key}/{flag_key}/environments/{environment_key}",
            headers=self.headers,
            json=patch_payload,
        )

        if response.status_code >= 400:
            print(
                f"❌ Error updating targeting rules for environment {environment_key}: {response.status_code}"
            )
            print(f"Response: {response.text}")
            response.raise_for_status()

        print(
            f"✅ Targeting rules for '{flag_key}' in environment '{environment_key}' updated successfully"
        )
        return response.json()
