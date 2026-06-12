# Varonis Sentinel Custom MCP Tools

Alpha-ready custom MCP tool collection for Varonis alert data in Microsoft Sentinel.

This repository is for a Varonis ISV developer, partner engineer, or joint customer team that wants an agent surface such as GitHub Copilot in VS Code, Copilot Studio, Foundry, Security Copilot, or a product-owned agent to call focused Varonis investigation tools over Sentinel data.

The repo does **not** ingest or generate telemetry. It assumes the customer already has the official Varonis SaaS connector sending production DatAlert alerts into Sentinel:

| Varonis source | Sentinel table queried by these tools | Required signal |
| --- | --- | --- |
| Varonis SaaS / DatAlert connector | `VaronisAlerts_CL` | Alert fields such as `Severity_s`, `Status_s`, `UserName_s`, `Asset_s`, `Query_s`, and workbook-era fields such as `AlertSeverity_s`, `ThreatDetectionPolicyName_s`, `UserNames_s`, `Assets_s`, `DeviceNames_s` |

These tools target the **Varonis SaaS** Sentinel connector. Other Varonis ingestion paths may land in different tables, such as `CommonSecurityLog` for older CEF/Syslog flows or `VaronisResources_CL` for resource-oriented connectors; those are intentionally out of scope for this alpha.

## What this publishes

`scripts/publish-mcp-tools.py` calls the Sentinel Platform Services authoring API and publishes each file in `mcp-tools/*.kql` as a Kqs custom MCP tool under one collection, defaulting to:

```text
Varonis-Sentinel-MCP-Tools
```

Runtime endpoint:

```text
https://sentinel.microsoft.com/mcp/custom/Varonis-Sentinel-MCP-Tools/
```

## Tools

| Tool | Main table | What it answers |
| --- | --- | --- |
| `Varonis_Alert_Posture` | `VaronisAlerts_CL` | What is the 24h Varonis alert posture: alert volume, severity/status mix, open alerts, sensitive-data alerts, users, assets, policies, and first/last seen times? |
| `Varonis_High_Severity_Alert_Triage` | `VaronisAlerts_CL` | Which high or critical Varonis alerts need investigation first, and what users/assets/policies are involved? |
| `Varonis_User_Alert_Investigation` | `VaronisAlerts_CL` | For a supplied `UserName`, what Varonis alerts, assets, policies, severities, and statuses are tied to that user? |
| `Varonis_Asset_Exposure_Investigation` | `VaronisAlerts_CL` | For a supplied `AssetName`, what alerts, users, policies, domains, platforms, and sensitive-data flags are tied to that asset? |
| `Varonis_Threat_Policy_Hotspots` | `VaronisAlerts_CL` | Which Varonis threat detection policies are generating the most high-severity/open alerts? |
| `Varonis_Sensitive_Data_Exposure` | `VaronisAlerts_CL` | Which assets with sensitive or flagged data are involved in alerts, and which users/policies are driving exposure? |
| `Varonis_Open_Alert_Aging` | `VaronisAlerts_CL` | Which open or under-investigation Varonis alerts are aging and should be chased? |

For detailed usage, input arguments, KQL strategy, and expected output shape, see [`docs/tool-reference.md`](docs/tool-reference.md).

## Prerequisites

1. A Microsoft Sentinel workspace with Sentinel Platform Services / data lake enabled.
2. Production Varonis connector data already flowing into `VaronisAlerts_CL`.
3. Azure CLI authenticated to the tenant that owns the Sentinel workspace:
   ```bash
   az login
   az account set --subscription "<subscription-id-or-name>"
   ```
4. Permission to author custom MCP collections in Sentinel Platform Services.
5. Python 3.9+.

This is an alpha/private-preview style surface. The publisher and runtime both use the Sentinel Platform Services resource ID `4500ebfb-89b6-4b14-a480-7f749797bfcd`. In practice:

- The tenant must have Microsoft Sentinel data lake and the required Microsoft Defender / Sentinel Platform Services licensing enabled.
- To **create, update, or delete** custom tools, use an identity with Security Operator, Security Administrator, or Global Administrator privileges for the Microsoft Security experience plus read access to the target Sentinel workspace.
- To **list or invoke** the tools, use an identity with Security Reader or Global Reader privileges plus read access to the target Sentinel workspace.
- If API publishing is unavailable in your tenant, create the same KQL as custom tools through the Microsoft Defender portal / Advanced hunting "Save as tool" flow, then use the same runtime endpoint pattern.

## Publish the tools through the API

Clone this repo, install dependencies, and publish:

```bash
git clone https://github.com/MitchellGulledge3/varonis-sentinel-mcp-tools.git
cd varonis-sentinel-mcp-tools

python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

python3 scripts/publish-mcp-tools.py \
  --collection Varonis-Sentinel-MCP-Tools \
  --workspace-id "<workspace-customer-id>"
```

Use `--dry-run` first if you want to inspect the API payloads without writing anything:

```bash
python3 scripts/publish-mcp-tools.py \
  --collection Varonis-Sentinel-MCP-Tools \
  --workspace-id "<workspace-customer-id>" \
  --dry-run
```

The script is idempotent: it tolerates an existing collection and uses `PUT` for each tool, so rerunning updates the tool definitions.

## Quick start for Claude Code

```bash
TOKEN=$(az account get-access-token \
  --resource 4500ebfb-89b6-4b14-a480-7f749797bfcd \
  --query accessToken -o tsv)

python3 scripts/write-claude-mcp-config.py \
  --collection Varonis-Sentinel-MCP-Tools \
  --bearer-token "$TOKEN"
```

Suggested Claude Code prompt:

```text
Read this repo. Use the Varonis-Sentinel-MCP-Tools MCP server from .mcp.json.
List the available tools, then call them for workspace <workspace-customer-id>.
```

## Run locally from the terminal

1. Copy environment template:
   ```bash
   cp .env.example .env
   ```

2. Edit `.env`:
   ```text
   SENTINEL_MCP_COLLECTION=Varonis-Sentinel-MCP-Tools
   MCP_DEFAULT_ARGUMENTS={"workspaceId":"<workspace-customer-id>"}
   MCP_TOOL_ARGUMENT_TEMPLATE={}
   VARONIS_USER_NAME=<user@domain.com>
   VARONIS_ASSET_NAME=<asset-or-path>
   ```

3. Ask GitHub Copilot, Claude, or another coding agent to use this repo. Suggested prompt:
   ```text
   Look at this repository and help me install and run the Varonis Sentinel custom MCP tools locally.
   Use scripts/publish-mcp-tools.py to publish the tools through the Sentinel Platform Services API,
   then use run_tools.py to call the custom MCP endpoint from this machine.
   ```

4. Run a tool through the local terminal runner:
   ```bash
   python3 run_tools.py --prompt "Summarize Varonis alert posture" --show-raw
   python3 run_tools.py --prompt "Investigate Varonis alerts for alice@example.com" --show-raw
   python3 run_tools.py --prompt "Investigate Varonis asset 'finance/share'" --show-raw
   ```

The runner calls the real custom MCP endpoint at `https://sentinel.microsoft.com/mcp/custom/<collection>/` using Azure credentials. It does not use generated telemetry.

## Run locally from VS Code / GitHub Copilot

VS Code needs an MCP server registration that includes an access token for Sentinel Platform Services. Generate a short-lived config from your current Azure CLI session:

```bash
TOKEN=$(az account get-access-token \
  --resource 4500ebfb-89b6-4b14-a480-7f749797bfcd \
  --query accessToken -o tsv)

python3 scripts/write-vscode-mcp-config.py \
  --collection Varonis-Sentinel-MCP-Tools \
  --bearer-token "$TOKEN"
```

This writes `.vscode/mcp.json` with the HTTP MCP endpoint and `Authorization: Bearer <token>` header. The file is gitignored because it contains a bearer token. When the token expires, rerun the command above.

Then open `.vscode/mcp.json` in VS Code, start the MCP server from the CodeLens/command UI, and ask Copilot Chat to list or call tools from `Varonis-Sentinel-MCP-Tools`. Use prompts such as:

```text
Use the Varonis Sentinel MCP tools to summarize alert posture for workspace <workspace-customer-id>.
Use Varonis_User_Alert_Investigation for user alice@example.com in workspace <workspace-customer-id>.
Use Varonis_Asset_Exposure_Investigation for asset finance/share in workspace <workspace-customer-id>.
```

## Configure an MCP-capable agent

Register this remote MCP endpoint in any MCP-capable agent runtime that supports authenticated HTTP MCP servers:

```text
https://sentinel.microsoft.com/mcp/custom/Varonis-Sentinel-MCP-Tools/
```

At runtime, every tool requires:

```json
{
  "workspaceId": "<workspace-customer-id>"
}
```

`Varonis_User_Alert_Investigation` also requires:

```json
{
  "UserName": "alice@example.com"
}
```

`Varonis_Asset_Exposure_Investigation` also requires:

```json
{
  "AssetName": "finance/share"
}
```

`workspaceId` is the workspace customer ID the Sentinel custom MCP runtime uses to bind the KQL execution target. The KQL text itself does not call `workspace("<id>")`; target selection is handled by the platform tool runtime.

## Repository map

| Path | Purpose |
| --- | --- |
| `mcp-tools/*.kql` | Production-table KQL definitions published as custom MCP tools |
| `scripts/publish-mcp-tools.py` | API publisher for the Sentinel custom MCP collection |
| `scripts/write-claude-mcp-config.py` | Writes a gitignored Claude Code `.mcp.json` config |
| `scripts/write-vscode-mcp-config.py` | Writes a gitignored VS Code MCP config with a short-lived bearer token |
| `run_tools.py` | Local runner that selects a tool from a natural-language prompt and calls the custom MCP endpoint |
| `sentinel_mcp_tools/client.py` | Minimal JSON-RPC client for Sentinel custom MCP endpoints |
| `docs/tool-reference.md` | Deep explanation of every tool and how agents should use it |
| `docs/sample-output.md` | Captured/sanitized sample output from local runs |
| `docs/runbook.md` | Alpha handoff runbook for ISV and customer teams |


## Troubleshooting

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| Tools publish but return no rows | No rows in CCF tables for the last 24h | Confirm production ingestion or adjust the `lookback` variable in the KQL files |
| Claude Code 401/403 | Token expired or identity lacks access | Regenerate `.mcp.json` with a fresh token and verify Sentinel roles |
| Empty result for specific entity | Entity name mismatch | Check capitalization or exact spelling, though tools try to tolerate case differences |

## Notes for alpha users

- The tools are read-only KQL tools.
- Most tools query the last 24 hours by design; `Varonis_Open_Alert_Aging` uses seven days to find older open alerts.
- They are intentionally table-specific and do not try to become a general Varonis chatbot.
- If a workspace has no Varonis rows in `VaronisAlerts_CL`, the tools execute but return zero-row or zero-count output.
- The tools tolerate both connector-documented fields (`Severity_s`, `Status_s`, `UserName_s`, `Asset_s`) and workbook-era fields (`AlertSeverity_s`, `ThreatDetectionPolicyName_s`, `UserNames_s`, `Assets_s`, `DeviceNames_s`) where possible.
