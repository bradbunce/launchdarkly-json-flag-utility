"""FastAPI web application for LaunchDarkly JSON Flag Utility."""

import os
import json

import boto3
import ldclient
from ldclient import Context
from ldclient.config import Config
from dotenv import load_dotenv
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from ldai import LDAIClient, AICompletionConfigDefault

from ld_json_flag.client import LaunchDarklyClient

load_dotenv()

# --- LaunchDarkly REST API client (flag management) ---
LD_API_KEY = os.environ.get("LD_API_KEY")
DEFAULT_PROJECT_KEY = os.environ.get("LD_PROJECT_KEY")
flag_client = LaunchDarklyClient(LD_API_KEY, DEFAULT_PROJECT_KEY)

# --- LaunchDarkly Server SDK (AI Configs) ---
LD_SDK_KEY = os.environ.get("LD_SDK_KEY")
ldclient.set_config(Config(LD_SDK_KEY))
ld_client = ldclient.get()
ai_client = LDAIClient(ld_client)

AI_CONFIG_KEY = "json-validation-assistant"

# --- AWS Bedrock client ---
bedrock_client = boto3.client(
    "bedrock-runtime",
    region_name=os.environ.get("AWS_REGION", None),
)

# --- Current project state ---
current_project_key = DEFAULT_PROJECT_KEY

# --- FastAPI app ---
app = FastAPI(title="LaunchDarkly JSON Flag Utility")

templates_dir = os.path.join(os.path.dirname(__file__), "templates")
static_dir = os.path.join(os.path.dirname(__file__), "static")

templates = Jinja2Templates(directory=templates_dir)
app.mount("/static", StaticFiles(directory=static_dir), name="static")


def get_json_flags(project_key):
    """Fetch all JSON feature flags and their validation status."""
    flags = flag_client.get_feature_flags(project_key)
    json_flags = []

    for flag in flags:
        flag_details = flag_client.get_feature_flag(flag.get("key"), project_key)
        variations = flag_details.get("variations", [])

        has_json = False
        for variation in variations:
            if isinstance(variation.get("value"), dict):
                has_json = True
                break

        if has_json:
            # Validate each variation
            flag_info = {
                "key": flag.get("key"),
                "name": flag.get("name"),
                "variations": [],
                "is_valid": True,
            }
            for variation in variations:
                value = variation.get("value", {})
                var_info = {
                    "name": variation.get("name", "Unnamed"),
                    "value": value,
                    "is_valid": True,
                    "error": None,
                }
                if isinstance(value, dict):
                    try:
                        flag_client.validate_tcp_port_json(value)
                    except ValueError as e:
                        var_info["is_valid"] = False
                        var_info["error"] = str(e)
                        flag_info["is_valid"] = False
                flag_info["variations"].append(var_info)
            json_flags.append(flag_info)

    return json_flags


def inference_config_from_params(params):
    """Map AI Config parameters to Bedrock's Converse inferenceConfig shape."""
    mapping = {"max_tokens": "maxTokens"}
    allowed = {"maxTokens", "temperature", "topP", "stopSequences"}
    renamed = {mapping.get(k, k): v for k, v in (params or {}).items()}
    return {k: v for k, v in renamed.items() if k in allowed}


@app.get("/", response_class=HTMLResponse)
async def dashboard(request: Request):
    """Main dashboard — renders immediately with a loading state."""
    return templates.TemplateResponse(
        request,
        "dashboard.html",
        {},
    )


@app.get("/load", response_class=HTMLResponse)
async def load_app(request: Request):
    """Load projects and flags asynchronously after the page renders."""
    global current_project_key
    projects = flag_client.get_projects()

    # If no default project key is set, use the first project
    if not current_project_key and projects:
        current_project_key = projects[0].get("key")

    json_flags = get_json_flags(current_project_key) if current_project_key else []
    return templates.TemplateResponse(
        request,
        "partials/app_content.html",
        {
            "flags": json_flags,
            "project_key": current_project_key,
            "projects": projects,
        },
    )


@app.post("/switch-project", response_class=HTMLResponse)
async def switch_project(request: Request):
    """Switch the active project."""
    global current_project_key
    form = await request.form()
    new_project = form.get("project_key", current_project_key)
    current_project_key = new_project
    json_flags = get_json_flags(current_project_key)
    return templates.TemplateResponse(
        request,
        "partials/flag_list.html",
        {"flags": json_flags},
    )


@app.post("/validate", response_class=HTMLResponse)
async def validate_flags(request: Request):
    """Run validation and return results."""
    json_flags = get_json_flags(current_project_key)
    return templates.TemplateResponse(
        request,
        "partials/flag_list.html",
        {"flags": json_flags},
    )


@app.post("/fix/{flag_key}/{variation_index}", response_class=HTMLResponse)
async def ai_fix_suggestion(request: Request, flag_key: str, variation_index: int):
    """Get an AI-powered fix suggestion for an invalid variation."""
    # Get the flag details
    flag_details = flag_client.get_feature_flag(flag_key, current_project_key)
    variations = flag_details.get("variations", [])

    if variation_index >= len(variations):
        return HTMLResponse("<p class='error'>Variation not found</p>")

    variation = variations[variation_index]
    value = variation.get("value", {})
    var_name = variation.get("name", "Unnamed")

    # Get the validation error
    try:
        flag_client.validate_tcp_port_json(value)
        return HTMLResponse("<p class='success'>This variation is already valid.</p>")
    except ValueError as error:
        error_message = str(error)

    # Get AI Config from LaunchDarkly
    context = Context.builder("web-user").kind("user").name("Web UI").build()

    fallback = AICompletionConfigDefault(enabled=False)

    config = ai_client.completion_config(
        AI_CONFIG_KEY,
        context,
        fallback,
        {
            "flag_name": flag_details.get("name", flag_key),
            "flag_key": flag_key,
            "variation_name": var_name,
            "variation_value": json.dumps(value),
            "error_message": error_message,
        },
    )

    if not config.enabled:
        return HTMLResponse(
            "<p class='error'>AI Config is disabled. Check LaunchDarkly targeting.</p>"
        )

    tracker = config.create_tracker()
    messages = config.messages or []

    # Build Bedrock Converse request
    system_messages = [{"text": m.content} for m in messages if m.role == "system"]
    conversation = [
        {"role": m.role, "content": [{"text": m.content}]}
        for m in messages
        if m.role in ("user", "assistant")
    ]

    converse_params = {
        "modelId": (
            config.model.name
            if config.model.name.startswith(("us.", "eu.", "ap."))
            else f"us.{config.model.name}"
        ),
        "messages": conversation,
    }
    if system_messages:
        converse_params["system"] = system_messages

    ld_params = (
        config.model.to_dict().get("parameters") if config.model else None
    ) or {}
    inference = inference_config_from_params(ld_params)
    if inference:
        converse_params["inferenceConfig"] = inference

    # Call Bedrock
    try:
        response = tracker.track_bedrock_converse_metrics(
            bedrock_client.converse(**converse_params)
        )

        # Extract the response text
        output = response.get("output", {}).get("message", {})
        content_blocks = output.get("content", [])
        suggestion_text = ""
        for block in content_blocks:
            if "text" in block:
                suggestion_text += block["text"]

        # Strip markdown code fences if present
        suggestion_text = suggestion_text.strip()
        if suggestion_text.startswith("```"):
            lines = suggestion_text.split("\n")
            # Remove first line (```json) and last line (```)
            lines = [l for l in lines if not l.strip().startswith("```")]
            suggestion_text = "\n".join(lines).strip()

        # Try to parse as JSON to validate the suggestion
        try:
            suggested_value = json.loads(suggestion_text)
            suggestion_valid = True
            # Validate the suggestion
            try:
                flag_client.validate_tcp_port_json(suggested_value)
            except ValueError:
                suggestion_valid = False
        except json.JSONDecodeError:
            suggested_value = suggestion_text
            suggestion_valid = False

        return templates.TemplateResponse(
            request,
            "partials/ai_suggestion.html",
            {
                "suggestion": (
                    json.dumps(suggested_value, indent=2)
                    if isinstance(suggested_value, dict)
                    else suggestion_text
                ),
                "suggestion_valid": suggestion_valid,
                "flag_key": flag_key,
                "variation_index": variation_index,
            },
        )
    except Exception as e:
        return HTMLResponse(f"<p class='error'>AI error: {str(e)}</p>")


@app.post("/apply-fix/{flag_key}/{variation_index}", response_class=HTMLResponse)
async def apply_fix(request: Request, flag_key: str, variation_index: int):
    """Apply an AI-suggested fix to a flag variation."""
    form = await request.form()
    suggested_value = form.get("suggested_value")

    try:
        new_value = json.loads(suggested_value)
    except json.JSONDecodeError:
        return HTMLResponse("<p class='error'>Invalid JSON in suggestion</p>")

    # Validate the new value
    try:
        flag_client.validate_tcp_port_json(new_value)
    except ValueError as e:
        return HTMLResponse(f"<p class='error'>Suggestion is invalid: {str(e)}</p>")

    # Get current variations and update the specific one
    flag_details = flag_client.get_feature_flag(flag_key, current_project_key)
    variations = flag_details.get("variations", [])

    if variation_index >= len(variations):
        return HTMLResponse("<p class='error'>Variation not found</p>")

    variations[variation_index]["value"] = new_value

    # Update via API
    try:
        flag_client.update_flag_variations(flag_key, variations, current_project_key)
        return HTMLResponse(
            "<p class='success'>✅ Fix applied successfully! Refresh to see updated status.</p>"
        )
    except Exception as e:
        return HTMLResponse(f"<p class='error'>Error applying fix: {str(e)}</p>")


@app.post("/update-variation/{flag_key}/{variation_index}", response_class=HTMLResponse)
async def update_variation(request: Request, flag_key: str, variation_index: int):
    """Update a flag variation with user-edited JSON value."""
    form = await request.form()
    raw_value = form.get("value", "")

    # Parse the JSON
    try:
        new_value = json.loads(raw_value)
    except json.JSONDecodeError as e:
        return HTMLResponse(f"<p class='error'>Invalid JSON: {str(e)}</p>")

    # Validate the new value
    try:
        flag_client.validate_tcp_port_json(new_value)
    except ValueError as e:
        return HTMLResponse(f"<p class='error'>Validation failed: {str(e)}</p>")

    # Get current variations and update the specific one
    flag_details = flag_client.get_feature_flag(flag_key, current_project_key)
    variations = flag_details.get("variations", [])

    if variation_index >= len(variations):
        return HTMLResponse("<p class='error'>Variation not found</p>")

    variations[variation_index]["value"] = new_value

    # Update via LaunchDarkly API
    try:
        flag_client.update_flag_variations(flag_key, variations, current_project_key)
        return HTMLResponse(
            "<p class='success'>✅ Saved successfully! Refresh to see updated status.</p>"
        )
    except Exception as e:
        return HTMLResponse(f"<p class='error'>Error saving: {str(e)}</p>")


@app.on_event("shutdown")
async def shutdown():
    """Clean up LaunchDarkly client on shutdown."""
    ld_client.flush()
    ld_client.close()
