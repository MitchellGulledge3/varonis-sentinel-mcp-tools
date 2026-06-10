from __future__ import annotations

"""Interactive terminal runner for the Varonis Sentinel custom MCP tools."""

import argparse
import asyncio
import json
import os
import re
from typing import Any

from dotenv import load_dotenv

from sentinel_mcp_tools.client import MCPToolResult, SentinelMCPClient


VARONIS_TOOLS = {
    "posture": "Varonis_Alert_Posture",
    "high_severity": "Varonis_High_Severity_Alert_Triage",
    "user": "Varonis_User_Alert_Investigation",
    "asset": "Varonis_Asset_Exposure_Investigation",
    "policy": "Varonis_Threat_Policy_Hotspots",
    "sensitive": "Varonis_Sensitive_Data_Exposure",
    "aging": "Varonis_Open_Alert_Aging",
}

TOOL_ROUTES = [
    (("user", "account", "upn", "sam", "investigate user"), VARONIS_TOOLS["user"]),
    (("asset", "file", "folder", "share", "device", "investigate asset"), VARONIS_TOOLS["asset"]),
    (("high", "critical", "severe", "triage"), VARONIS_TOOLS["high_severity"]),
    (("policy", "hotspot", "threat detection", "rule"), VARONIS_TOOLS["policy"]),
    (("sensitive", "classified", "confidential", "exposure", "flagged data"), VARONIS_TOOLS["sensitive"]),
    (("aging", "stale", "open", "old", "under investigation"), VARONIS_TOOLS["aging"]),
]

EXAMPLE_PROMPTS = [
    "Summarize Varonis alert posture",
    "Show high severity Varonis alerts",
    "Investigate Varonis alerts for alice@example.com",
    "Investigate Varonis asset finance/share",
    "Show Varonis threat policy hotspots",
    "Show sensitive data exposure from Varonis",
    "Show aging open Varonis alerts",
]


def parse_json_env(name: str, default: dict[str, Any]) -> dict[str, Any]:
    raw = os.getenv(name)
    if not raw:
        return default
    try:
        value = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise ValueError(f"{name} must be valid JSON: {exc}") from exc
    if not isinstance(value, dict):
        raise ValueError(f"{name} must be a JSON object.")
    return value


def extract_user(message: str) -> str:
    match = re.search(r"[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}", message)
    if match:
        return match.group(0)
    fallback = os.getenv("VARONIS_USER_NAME")
    if not fallback:
        raise ValueError("User investigation requires a UPN in the prompt or VARONIS_USER_NAME in the environment.")
    return fallback


def extract_asset(message: str) -> str:
    quoted = re.search(r"['\"]([^'\"]+)['\"]", message)
    if quoted:
        return quoted.group(1)
    fallback = os.getenv("VARONIS_ASSET_NAME")
    if fallback:
        return fallback
    words = message.split()
    return words[-1] if words else ""


def render_arguments(message: str, tool_name: str, template: str, defaults: dict[str, Any]) -> dict[str, Any]:
    rendered = template.replace("{message}", message)
    try:
        args = json.loads(rendered)
    except json.JSONDecodeError as exc:
        raise ValueError(f"MCP_TOOL_ARGUMENT_TEMPLATE rendered invalid JSON: {exc}") from exc
    if not isinstance(args, dict):
        raise ValueError("MCP_TOOL_ARGUMENT_TEMPLATE must render to a JSON object.")
    merged = {**args, **defaults}
    if tool_name == VARONIS_TOOLS["user"]:
        merged.setdefault("UserName", extract_user(message))
    if tool_name == VARONIS_TOOLS["asset"]:
        merged.setdefault("AssetName", extract_asset(message))
    return merged


def select_tool(prompt: str) -> str:
    configured = os.getenv("SENTINEL_MCP_TOOL", "").strip()
    prompt_lower = prompt.lower()
    if re.search(r"[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}", prompt):
        return VARONIS_TOOLS["user"]
    for keywords, tool_name in TOOL_ROUTES:
        if any(keyword in prompt_lower for keyword in keywords):
            return tool_name
    return configured or VARONIS_TOOLS["posture"]


def create_mcp_client() -> SentinelMCPClient:
    return SentinelMCPClient(
        collection=os.getenv("SENTINEL_MCP_COLLECTION"),
        server_url=os.getenv("SENTINEL_MCP_SERVER_URL"),
    )


async def run_prompt(prompt: str, *, show_raw: bool) -> None:
    tool_name = select_tool(prompt)
    template = os.getenv("MCP_TOOL_ARGUMENT_TEMPLATE", "{}")
    defaults = parse_json_env("MCP_DEFAULT_ARGUMENTS", {})
    arguments = render_arguments(prompt, tool_name, template, defaults)

    print(f"\nPrompt: {prompt}")
    print(f"Tool:   {tool_name}")
    print(f"Args:   {json.dumps(arguments, sort_keys=True)}")
    print("Status: calling Sentinel MCP...\n")

    client = create_mcp_client()
    await client.connect()
    try:
        result: MCPToolResult = await client.call_tool(tool_name, arguments)
    finally:
        await client.close()

    raw_text = result.text or json.dumps(result.content, indent=2)
    print("Result")
    print("------")
    print(raw_text)


async def interactive_loop(show_raw: bool) -> None:
    print("Varonis Sentinel Custom MCP Tool Runner")
    print("Type a prompt and press Enter. Type 'examples' to list prompts or 'quit' to exit.\n")
    print("Examples:")
    for prompt in EXAMPLE_PROMPTS:
        print(f"  - {prompt}")

    while True:
        try:
            prompt = input("\nvaronis-mcp> ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            return

        if not prompt:
            continue
        if prompt.lower() in {"quit", "exit", "q"}:
            return
        if prompt.lower() == "examples":
            for example in EXAMPLE_PROMPTS:
                print(f"  - {example}")
            continue

        try:
            await run_prompt(prompt, show_raw=show_raw)
        except Exception as exc:
            print(f"Error: {exc}")


def main() -> None:
    load_dotenv()
    parser = argparse.ArgumentParser(description="Run the Varonis Sentinel custom MCP terminal client.")
    parser.add_argument("--prompt", help="Run one prompt and exit instead of starting the interactive loop.")
    parser.add_argument("--show-raw", action="store_true", help="Print the formatted raw MCP/Kusto result.")
    args = parser.parse_args()

    if args.prompt:
        asyncio.run(run_prompt(args.prompt, show_raw=args.show_raw))
    else:
        asyncio.run(interactive_loop(show_raw=args.show_raw))


if __name__ == "__main__":
    main()
