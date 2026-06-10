from __future__ import annotations

"""Publish Varonis production-table KQL files as Microsoft Sentinel custom MCP tools."""

import argparse
import json
import pathlib
import re
import subprocess
import sys
import urllib.error
import urllib.request

SENTINEL_RESOURCE_ID = "4500ebfb-89b6-4b14-a480-7f749797bfcd"
API_BASE = "https://api.securityplatform.microsoft.com/aiprimitives/mcpToolCollections"

DESCRIPTIONS = {
    "Varonis_Alert_Posture": "Summarize production Varonis alert posture from VaronisAlerts_CL: alert volume, severity mix, status mix, sensitive-data alerts, users, assets, policies, and first/last seen times.",
    "Varonis_High_Severity_Alert_Triage": "List recent high or critical Varonis alerts with alert ID, severity, status, policy, affected users/assets, platform, domain, sensitive-data flag, and query context.",
    "Varonis_User_Alert_Investigation": "Investigate Varonis alerts for a supplied user, including severity, status, sensitive-data involvement, affected assets, policies, and a risk score.",
    "Varonis_Asset_Exposure_Investigation": "Investigate Varonis alerts for a supplied asset, including users, policies, platform, file server/domain, sensitive-data involvement, and exposure score.",
    "Varonis_Threat_Policy_Hotspots": "Rank Varonis threat detection policies by alert volume, high-severity count, open alerts, alerted events, users, and assets.",
    "Varonis_Sensitive_Data_Exposure": "Surface Varonis alerts involving sensitive or flagged data by asset, users, policies, platform, file server/domain, severity, and status.",
    "Varonis_Open_Alert_Aging": "Find aging open Varonis alerts from the last seven days, grouped by policy and status with max/average age and high-severity counts.",
}

ARGUMENT_DESCRIPTIONS = {
    "UserName": "Varonis user name, UPN, SAM account name, or identifying user substring to investigate.",
    "AssetName": "Varonis asset name, file path, share, device, or identifying asset substring to investigate.",
}

PLACEHOLDER_PATTERN = re.compile(r"(?<!{){\s*([A-Za-z_][A-Za-z0-9_]*)\s*}(?!})")


def az_token() -> str:
    completed = subprocess.run(
        ["az", "account", "get-access-token", "--resource", SENTINEL_RESOURCE_ID, "--query", "accessToken", "-o", "tsv"],
        check=True,
        capture_output=True,
        text=True,
    )
    return completed.stdout.strip()


def request(method: str, url: str, token: str, payload: dict, *, allow_conflict: bool = False) -> dict:
    body = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=body,
        method=method,
        headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(req) as response:
            return json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        details = exc.read().decode("utf-8", errors="replace")
        if allow_conflict and exc.code == 409:
            return {"status": "exists", "details": details}
        raise RuntimeError(f"{method} {url} failed: HTTP {exc.code}: {details}") from exc


def tool_payload(collection: str, workspace_id: str, query_path: pathlib.Path) -> dict:
    name = query_path.stem
    query_format = query_path.read_text().strip()
    placeholders = sorted({match.group(1) for match in PLACEHOLDER_PATTERN.finditer(query_format)})
    argument_properties = {
        "workspaceId": {"type": "string", "description": "Log Analytics workspace/customer ID to query."}
    }
    required_arguments = ["workspaceId"]
    for placeholder in placeholders:
        if placeholder == "workspaceId":
            continue
        argument_properties[placeholder] = {
            "type": "string",
            "description": ARGUMENT_DESCRIPTIONS.get(placeholder, f"Value to substitute for {placeholder}."),
        }
        required_arguments.append(placeholder)

    return {
        "name": name,
        "title": name.replace("_", " "),
        "description": DESCRIPTIONS.get(name, f"Run the {name.replace('_', ' ')} KQL investigation."),
        "collectionName": collection,
        "properties": {
            "mcpToolType": "Kqs",
            "queryFormat": query_format,
            "arguments": {
                "type": "object",
                "properties": argument_properties,
                "required": required_arguments,
            },
            "defaultArgumentValues": {"workspaceId": workspace_id},
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Publish production Varonis KQL files as Sentinel custom MCP tools.")
    parser.add_argument("--collection", default="Varonis-Sentinel-MCP-Tools")
    parser.add_argument("--workspace-id", required=True)
    parser.add_argument("--tools-dir", default=str(pathlib.Path(__file__).parents[1] / "mcp-tools"))
    parser.add_argument("--dry-run", action="store_true", help="Print collection/tool payloads without calling the Sentinel authoring API.")
    args = parser.parse_args()

    collection_payload = {
        "name": args.collection,
        "title": "Varonis Sentinel Custom MCP Tools",
        "description": "Custom Sentinel MCP tools for production Varonis alert posture, high-severity triage, user and asset investigations, policy hotspots, sensitive-data exposure, and open-alert aging.",
    }
    print(f"Publishing collection: {args.collection}")
    if args.dry_run:
        print(json.dumps(collection_payload, indent=2))
        token = ""
    else:
        token = az_token()
        print(json.dumps(request("PUT", f"{API_BASE}/{args.collection}", token, collection_payload, allow_conflict=True), indent=2))

    for query_path in sorted(pathlib.Path(args.tools_dir).glob("*.kql")):
        payload = tool_payload(args.collection, args.workspace_id, query_path)
        print(f"\nPublishing tool: {payload['name']}")
        if args.dry_run:
            print(json.dumps(payload, indent=2))
        else:
            print(json.dumps(request("PUT", f"{API_BASE}/{args.collection}/tools/{payload['name']}", token, payload), indent=2))

    return 0


if __name__ == "__main__":
    sys.exit(main())
