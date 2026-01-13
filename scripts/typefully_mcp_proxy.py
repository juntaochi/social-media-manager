import sys
import json
import copy
import os
from typing import Any

import requests

TYPEFULLY_MCP_URL = "https://mcp.typefully.com/mcp"


def fix_schema_for_google(obj: Any) -> Any:
    """
    Recursively fix JSON schema for Google Gemini API compatibility:
    1. Convert boolean const/enum to strings
    2. Add missing "type" fields (Google requires explicit types)
    3. Remove unsupported keywords (oneOf, anyOf, allOf, discriminator)
    """
    if isinstance(obj, dict):
        result = {}
        
        for key, value in obj.items():
            if key in ("oneOf", "anyOf"):
                # Google doesn't support oneOf/anyOf - flatten to first option or object
                if isinstance(value, list) and len(value) > 0:
                    # Find the non-null option
                    for option in value:
                        if isinstance(option, dict) and option.get("type") != "null":
                            flattened = fix_schema_for_google(option)
                            result.update(flattened)
                            break
                    else:
                        # All options are null or empty, default to string
                        result["type"] = "string"
                continue
            elif key == "allOf":
                # Merge allOf schemas
                if isinstance(value, list):
                    for item in value:
                        if isinstance(item, dict):
                            result.update(fix_schema_for_google(item))
                continue
            elif key == "discriminator":
                # Google doesn't support discriminator
                continue
            elif key == "enum" and isinstance(value, list):
                result[key] = [
                    str(v).lower() if isinstance(v, bool) else v 
                    for v in value
                ]
            elif key == "const" and isinstance(value, bool):
                result[key] = str(value).lower()
            elif key == "type" and value == "boolean":
                if "const" in obj or "enum" in obj:
                    result[key] = "string"
                else:
                    result[key] = value
            else:
                result[key] = fix_schema_for_google(value)
        
        # Ensure type is present for objects with properties
        if "properties" in result and "type" not in result:
            result["type"] = "object"
        
        # Ensure type is present for arrays with items
        if "items" in result and "type" not in result:
            result["type"] = "array"
        
        # Fix boolean enums to have string type
        if "enum" in result or "const" in result:
            enum_vals = result.get("enum", [])
            const_val = result.get("const")
            has_string_bool = any(v in ["true", "false"] for v in enum_vals)
            if const_val in ["true", "false"]:
                has_string_bool = True
            if has_string_bool:
                result["type"] = "string"
        
        return result
    elif isinstance(obj, list):
        return [fix_schema_for_google(item) for item in obj]
    else:
        return obj


def fix_discriminator(discriminator: dict) -> dict:
    """
    Fix discriminator mappings: {"True": "..."} -> {"true": "..."}
    """
    result = copy.deepcopy(discriminator)
    if "mapping" in result and isinstance(result["mapping"], dict):
        new_mapping = {}
        for key, value in result["mapping"].items():
            if key in ["True", "False"]:
                new_mapping[key.lower()] = value
            else:
                new_mapping[key] = value
        result["mapping"] = new_mapping
    return result


def parse_sse_event(lines):
    """Parse SSE event lines into a dict with event type and data."""
    event_type = "message"
    data_content = ""
    
    for line in lines:
        if line.startswith("event:"):
            event_type = line[6:].strip()
        elif line.startswith("data:"):
            # SSE spec: data can span multiple lines
            data_content += line[5:].strip()
    
    if data_content:
        try:
            data = json.loads(data_content)
            return {"event": event_type, "data": data}
        except json.JSONDecodeError:
            return None
    return None


def forward_to_typefully_sse(api_key, request):
    """Forward request to Typefully MCP via SSE and return the response."""
    mcp_url = f"{TYPEFULLY_MCP_URL}?TYPEFULLY_API_KEY={api_key}"
    method = request.get("method", "")
    
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json, text/event-stream"
    }
    
    try:
        with requests.Session() as s:
            response = s.post(
                mcp_url,
                json=request,
                headers=headers,
                timeout=60,
                stream=True
            )
            
            if response.status_code != 200:
                return {
                    "jsonrpc": "2.0",
                    "id": request.get("id"),
                    "error": {
                        "code": -32603,
                        "message": f"HTTP {response.status_code}: {response.text[:500]}"
                    }
                }
            
            current_event_lines = []
            
            for line in response.iter_lines(decode_unicode=True):
                if line is None:
                    continue
                
                line = line.rstrip()
                if not line:
                    if current_event_lines:
                        event = parse_sse_event(current_event_lines)
                        if event and event.get("data") is not None:
                            result = event["data"]
                            
                            if method in ("tools/list", "initialize") and "result" in result:
                                result["result"] = fix_schema_for_google(result["result"])
                            
                            return result
                        current_event_lines = []
                else:
                    current_event_lines.append(line)
            
            return {
                "jsonrpc": "2.0",
                "id": request.get("id"),
                "error": {"code": -32603, "message": "No valid message event received from SSE stream"}
            }
            
    except Exception as e:
        return {
            "jsonrpc": "2.0",
            "id": request.get("id"),
            "error": {"code": -32603, "message": str(e)}
        }


def send_response(response):
    sys.stdout.write(json.dumps(response) + "\n")
    sys.stdout.flush()


def load_env_fallback():
    """Manually parse .env file if it exists and key is missing."""
    try:
        if os.path.exists(".env"):
            with open(".env", "r") as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith("#") and "=" in line:
                        key, value = line.split("=", 1)
                        if key.strip() == "TYPEFULLY_KEY":
                            return value.strip().strip("'").strip('"')
    except Exception:
        pass
    return None


def enforce_draft_only(request: dict) -> dict:
    if request.get("method") == "tools/call":
        params = request.get("params", {})
        tool_name = params.get("name")
        arguments = params.get("arguments", {})
        
        if tool_name in ("typefully_create_draft", "typefully_edit_draft"):
            if "requestBody" in arguments:
                rb = arguments["requestBody"]
                if "publish_at" in rb:
                    del rb["publish_at"]
    return request


def run_proxy():
    api_key = os.environ.get("TYPEFULLY_API_KEY")
    if not api_key or api_key.startswith("{env:"):
        api_key = load_env_fallback()
    
    if not api_key and len(sys.argv) > 1:
        api_key = sys.argv[1]
    
    if not api_key or api_key.startswith("{env:"):
        sys.exit(1)
    
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        
        try:
            request = json.loads(line)
            method = request.get("method", "")
            request_id = request.get("id")
            
            request = enforce_draft_only(request)
            
            if method == "notifications/initialized":
                forward_to_typefully_sse(api_key, request)
                continue
            
            response = forward_to_typefully_sse(api_key, request)
            if request_id is not None:
                send_response(response)
                
        except json.JSONDecodeError:
            pass
        except Exception:
            pass


def main():
    run_proxy()


if __name__ == "__main__":
    main()

