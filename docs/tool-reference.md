# Varonis Custom MCP Tool Reference

These tools are designed for agents that need precise, callable Sentinel capabilities over production Varonis DatAlert data. Each tool is a Kqs tool published through the Sentinel Platform Services custom MCP API.

## Shared design choices

- **Primary table:** `VaronisAlerts_CL`.
- **Connector source:** official `Solutions/VaronisSaaS` Sentinel connector.
- **Workbook compatibility:** tools tolerate both documented connector fields and workbook-era fields where possible.
- **Missing-table behavior:** tools use `union isfuzzy=true` source aliases so alpha customers can publish/run them before `VaronisAlerts_CL` is present.
- **Authentication:** the consuming agent authenticates to Sentinel MCP; the tools themselves are read-only KQL.
- **Workspace binding:** every tool requires `workspaceId`. The Sentinel custom MCP runtime uses that argument to bind the KQL execution target; the KQL files do not call `workspace("<id>")` directly.
- **Parameter syntax:** Kqs tools use single-brace placeholders such as `{UserName}` and `{AssetName}` in `queryFormat`. The publisher detects those placeholders and declares matching tool arguments.

## `Varonis_Alert_Posture`

**Question answered:** "What is our Varonis alert posture in the last 24 hours?"

**Reads:** `VaronisAlerts_CL`

**Important fields:** `AlertSeverity_s`, `Severity_s`, `Status_s`, `AlertStatus_s`, `ThreatDetectionPolicyName_s`, `Name_s`, `Category`, `UserNames_s`, `UserName_s`, `SamAccountName_s`, `Assets_s`, `Asset_s`, `DeviceNames_s`, `AssetContainsSensitiveData_s`, `AssetContainsFlaggedData_s`.

**What it does:**

1. Normalizes severity, status, policy, user evidence, asset evidence, and sensitive-data flags.
2. Counts alerts, high-severity alerts, medium alerts, open alerts, and sensitive-data alerts.
3. Summarizes users, assets, policies, statuses, and first/last seen times.

**Best caller prompt:** "Summarize Varonis alert posture for this Sentinel workspace."

## `Varonis_High_Severity_Alert_Triage`

**Question answered:** "Which high or critical alerts need action first?"

**Reads:** `VaronisAlerts_CL`

**What it does:**

1. Filters high/critical alerts or numeric severities that map to high priority.
2. Projects alert ID, severity, status, policy, name, users, assets, platform, file server/domain, sensitive-data flag, event count, and query context.
3. Orders newest first and limits output to the top 50.

**Best caller prompt:** "Show high severity Varonis alerts."

## `Varonis_User_Alert_Investigation`

**Question answered:** "What Varonis alerts are tied to this user?"

**Required arguments:**

```json
{
  "workspaceId": "<workspace-customer-id>",
  "UserName": "alice@example.com"
}
```

**What it does:**

1. Matches the supplied user against `UserNames_s`, `UserName_s`, and `SamAccountName_s`.
2. Summarizes alerts, high-severity alerts, open alerts, sensitive-data alerts, event count, policies, assets, severities, statuses, and first/last seen.
3. Computes a simple risk score so agents can rank matching user evidence.

**Best caller prompt:** "Investigate Varonis alerts for alice@example.com."

## `Varonis_Asset_Exposure_Investigation`

**Question answered:** "What Varonis alerts are tied to this asset, share, path, or device?"

**Required arguments:**

```json
{
  "workspaceId": "<workspace-customer-id>",
  "AssetName": "finance/share"
}
```

**What it does:**

1. Matches the supplied asset substring against `Assets_s`, `Asset_s`, and `DeviceNames_s`.
2. Summarizes alerts, high-severity alerts, open alerts, sensitive-data alerts, event count, users, policies, platform, file server/domain, severities, statuses, and first/last seen.
3. Computes an exposure score.

**Best caller prompt:** "Investigate Varonis asset finance/share."

## `Varonis_Threat_Policy_Hotspots`

**Question answered:** "Which Varonis threat policies are generating the most actionable alerts?"

**Reads:** `VaronisAlerts_CL`

**What it does:**

1. Groups by `ThreatDetectionPolicyName_s`, `Name_s`, or `Category`.
2. Counts alerts, high-severity alerts, open alerts, alerted events, unique users, and unique assets.
3. Computes a hotspot score and returns the top 25 policies.

**Best caller prompt:** "Show Varonis threat policy hotspots."

## `Varonis_Sensitive_Data_Exposure`

**Question answered:** "Which sensitive-data assets are involved in Varonis alerts?"

**Reads:** `VaronisAlerts_CL`

**What it does:**

1. Uses `AssetContainsSensitiveData_s`, `AssetContainsFlaggedData_s`, and query text hints to identify sensitive/flagged-data alerts.
2. Groups by asset evidence.
3. Shows alerts, high-severity/open counts, users, policies, platform, file server/domain, severity/status mix, and first/last seen.

**Best caller prompt:** "Show sensitive data exposure from Varonis."

## `Varonis_Open_Alert_Aging`

**Question answered:** "Which open Varonis alerts are aging?"

**Reads:** `VaronisAlerts_CL`

**What it does:**

1. Uses a seven-day lookback to find alerts whose status contains `New`, `Open`, or `Under Investigation`.
2. Groups by policy and status.
3. Calculates max/average age in hours and highlights high-severity open alerts.

**Best caller prompt:** "Show aging open Varonis alerts."
