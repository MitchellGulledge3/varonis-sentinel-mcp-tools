# Alpha Handoff Runbook

Use this when handing the repo to a Varonis ISV engineer, partner engineer, or prospect customer.

## Goal

Publish a custom Sentinel MCP collection that exposes production Varonis alert investigation tools, then run those tools locally from VS Code/GitHub Copilot or another MCP-capable agent surface.

## Recommended agent prompt

Paste this into GitHub Copilot, Claude, or another coding assistant after cloning the repo:

```text
Review this repository and help me install the Varonis Sentinel custom MCP tools.
Use the README as the source of truth.
Publish the tools with scripts/publish-mcp-tools.py using my Sentinel workspace customer ID.
Then run run_tools.py to call the real Sentinel custom MCP endpoint locally.
Do not create generated telemetry. These tools should query the production VaronisAlerts_CL table.
```

## Step-by-step

1. Confirm production Varonis data is present:
   ```kql
   VaronisAlerts_CL
   | where TimeGenerated > ago(24h)
   | summarize Rows=count(), LastSeen=max(TimeGenerated)
   ```

2. Inspect the local field shape:
   ```kql
   VaronisAlerts_CL
   | take 5
   | project TimeGenerated, Severity_s, AlertSeverity_s, Status_s, ThreatDetectionPolicyName_s, UserName_s, UserNames_s, Asset_s, Assets_s, DeviceNames_s
   ```

3. Publish the collection:
   ```bash
   python3 scripts/publish-mcp-tools.py \
     --collection Varonis-Sentinel-MCP-Tools \
     --workspace-id "<workspace-customer-id>"
   ```

4. Run locally:
   ```bash
   cp .env.example .env
   # edit .env
   python3 run_tools.py --prompt "Summarize Varonis alert posture" --show-raw
   python3 run_tools.py --prompt "Investigate Varonis alerts for alice@example.com" --show-raw
   python3 run_tools.py --prompt "Investigate Varonis asset 'finance/share'" --show-raw
   ```

5. Register the custom MCP endpoint in the consuming agent:
   ```text
   https://sentinel.microsoft.com/mcp/custom/Varonis-Sentinel-MCP-Tools/
   ```

6. For VS Code/GitHub Copilot, generate `.vscode/mcp.json`:
   ```bash
   TOKEN=$(az account get-access-token \
     --resource 4500ebfb-89b6-4b14-a480-7f749797bfcd \
     --query accessToken -o tsv)

   python3 scripts/write-vscode-mcp-config.py \
     --collection Varonis-Sentinel-MCP-Tools \
     --bearer-token "$TOKEN"
   ```

   The generated file is intentionally gitignored because it contains a short-lived bearer token.

## Common failure modes

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| Tools publish but return no rows | Workspace has no Varonis rows in `VaronisAlerts_CL` for the lookback window | Confirm connector ingestion and widen a manual validation query outside the tool |
| User investigation returns no rows | User values are stored in a different field or format | Inspect `UserName_s`, `SamAccountName_s`, and `UserNames_s` with the field-shape query |
| Asset investigation returns no rows | Asset/path values are stored in a different field or format | Inspect `Asset_s`, `Assets_s`, and `DeviceNames_s` |
| HTTP 401/403 | Azure identity cannot call Sentinel Platform Services, lacks Security Operator/Admin for publishing, lacks Security Reader for invocation, lacks workspace read access, or the tenant is not enabled for the alpha surface | Re-authenticate with `az login`; verify license, role, and workspace access |
| `workspaceId` missing | Consuming agent did not pass required argument | Include the workspace customer ID in tool arguments |

## Positioning for an ISV or customer

These are not generic chat prompts. They are product-quality tool contracts that an agent can call deterministically:

- A Varonis product agent can call them to enrich its own alert view with Sentinel context.
- A customer Copilot can call them to triage Varonis alerts from inside a SOC workflow.
- A partner-built agent can use them as composable primitives for data security investigations.
