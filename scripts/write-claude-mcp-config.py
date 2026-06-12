from __future__ import annotations

"""Write a Claude Code .mcp.json config for the published Varonis Sentinel custom MCP collection."""

import argparse
import json
import pathlib


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate .mcp.json for Claude Code and the Varonis Sentinel custom MCP endpoint.")
    parser.add_argument("--collection", default="Varonis-Sentinel-MCP-Tools")
    parser.add_argument("--bearer-token", required=True, help="Access token for Sentinel Platform Services.")
    parser.add_argument("--output", default=".mcp.json")
    args = parser.parse_args()

    output = pathlib.Path(args.output)
    server_url = f"https://sentinel.microsoft.com/mcp/custom/{args.collection}/"
    payload = {
        "mcpServers": {
            args.collection: {
                "type": "http",
                "url": server_url,
                "headers": {
                    "Authorization": f"Bearer {args.bearer_token}",
                    "Content-Type": "application/json",
                    "Accept": "application/json, text/event-stream",
                },
            }
        }
    }
    output.write_text(json.dumps(payload, indent=2) + "\n")
    print(f"Wrote {output} for {server_url}")
    print("The bearer token is short-lived. Regenerate this file when the token expires.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
