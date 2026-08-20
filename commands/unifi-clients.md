---
description: List UniFi clients (wired and wireless) connected to a site, with optional filtering by MAC or hostname.
argument-hint: "[--site SITE_ID] [--filter SUBSTRING]"
allowed-tools: mcp__unifi__unifi_get_sites, mcp__unifi__unifi_get_clients
---

# /unifi-clients

List the UniFi clients connected to a site — wired, wireless, and guest.

## Usage

`/unifi-clients [--site SITE_ID] [--filter SUBSTRING]`

Arguments:

- `--site SITE_ID`: optional site ID to scope the query. Defaults to `default`. Validated against `mcp__unifi__unifi_get_sites`.
- `--filter SUBSTRING`: optional case-insensitive substring matched against MAC, hostname, IP, or ESSID. The filter runs client-side after the tool returns.

## Workflow

1. Call `mcp__unifi__unifi_get_sites` to resolve the default site if `--site` is not supplied.
2. Call `mcp__unifi__unifi_get_clients` with the resolved `site_id` to fetch the full client list.
3. If `--filter SUBSTRING` is supplied, narrow the result to entries where any of `mac`, `hostname`, `ip`, or `essid` contains the substring (case-insensitive).
4. Report: total count, filtered count, and a table of MAC, hostname, IP, signal (dBm for wireless), and uptime.
5. If the result is empty, report that explicitly and suggest verifying the site ID.

## Example

`/unifi-clients` — every client in the `default` site.

`/unifi-clients --site branch-office --filter "laptop"` — only clients whose hostname contains "laptop".
