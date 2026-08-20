---
description: Show a UniFi controller overview — list sites and surface per-site statistics (clients, devices, throughput, uptime).
argument-hint: [--site SITE_ID]
allowed-tools: mcp__unifi__unifi_get_sites, mcp__unifi__unifi_get_statistics
---

# /unifi-status

Print a UniFi controller status overview: which sites exist and the headline statistics for each (or one) site.

## Usage

`/unifi-status [--site SITE_ID]`

Arguments:

- `--site SITE_ID`: optional site ID to scope the report to a single site. Defaults to `default`. The `--site` flag must match one of the IDs returned by `mcp__unifi__unifi_get_sites`.

## Workflow

1. Call `mcp__unifi__unifi_get_sites` to enumerate the controller's sites. The first site ID becomes the default if `--site` is not supplied.
2. If `--site` is supplied, validate it against the sites list; if missing, surface the discrepancy and stop.
3. Call `mcp__unifi__unifi_get_statistics` with the resolved `site_id` to fetch the per-site statistics block.
4. Report: site ID(s), client count, device count, uplink throughput, and uptime summary.
5. If statistics returns an empty payload, report that explicitly and ask whether to retry with a different site.

## Example

`/unifi-status` — overview of every site, defaulting to the first.

`/unifi-status --site default` — single-site report.
