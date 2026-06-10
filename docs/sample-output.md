# Sample Output

Captured with `run_tools.py` calling the published `Varonis-Sentinel-MCP-Tools` custom MCP endpoint. Values are sanitized and representative of the result shapes an agent receives. The captured workspace had no production Varonis rows in `VaronisAlerts_CL`, so the previews intentionally show zero-row/zero-count behavior while proving that the published tools execute successfully.

## Publish payload validation

```text
Varonis_Alert_Posture: required=workspaceId
Varonis_Asset_Exposure_Investigation: required=workspaceId,AssetName
Varonis_High_Severity_Alert_Triage: required=workspaceId
Varonis_Open_Alert_Aging: required=workspaceId
Varonis_Sensitive_Data_Exposure: required=workspaceId
Varonis_Threat_Policy_Hotspots: required=workspaceId
Varonis_User_Alert_Investigation: required=workspaceId,UserName
tool_count=7
```

## `Varonis_Alert_Posture`

Prompt: `Summarize Varonis alert posture`

Arguments:

```json
{"workspaceId": "<workspace-customer-id>"}
```

Output preview:

```text
Alerts | HighSeverityAlerts | MediumSeverityAlerts | OpenAlerts | SensitiveDataAlerts | TotalAlertedEvents | UniqueUsers | UniqueAssets | Policies | Severities | Statuses | FirstSeen | LastSeen
-------+--------------------+----------------------+------------+---------------------+--------------------+-------------+--------------+----------+------------+----------+-----------+---------
0      | 0                  | 0                    | 0          | 0                   | 0.0                | 0           | 0            | []       | []         | []       | None      | None    

```

## `Varonis_High_Severity_Alert_Triage`

Prompt: `Show high severity Varonis alerts`

Arguments:

```json
{"workspaceId": "<workspace-customer-id>"}
```

Output preview:

```text
Query completed successfully, but returned no rows.

```

## `Varonis_User_Alert_Investigation`

Prompt: `Investigate Varonis alerts for alice@example.com`

Arguments:

```json
{"UserName": "alice@example.com", "workspaceId": "<workspace-customer-id>"}
```

Output preview:

```text
Query completed successfully, but returned no rows.

```

## `Varonis_Asset_Exposure_Investigation`

Prompt: `Investigate Varonis asset finance/share`

Arguments:

```json
{"AssetName": "finance/share", "workspaceId": "<workspace-customer-id>"}
```

Output preview:

```text
Query completed successfully, but returned no rows.

```

## `Varonis_Threat_Policy_Hotspots`

Prompt: `Show Varonis threat policy hotspots`

Arguments:

```json
{"workspaceId": "<workspace-customer-id>"}
```

Output preview:

```text
Query completed successfully, but returned no rows.

```

## `Varonis_Sensitive_Data_Exposure`

Prompt: `Show sensitive data exposure from Varonis`

Arguments:

```json
{"workspaceId": "<workspace-customer-id>"}
```

Output preview:

```text
Query completed successfully, but returned no rows.

```

## `Varonis_Open_Alert_Aging`

Prompt: `Show aging open Varonis alerts`

Arguments:

```json
{"workspaceId": "<workspace-customer-id>"}
```

Output preview:

```text
Query completed successfully, but returned no rows.

```
