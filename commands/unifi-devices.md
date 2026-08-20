---
description: List UniFi devices (access points, switches, gateways) at a site, with optional filtering by type or model.
argument-hint: "[--site SITE_ID] [--type ap|switch|gateway] [--filter SUBSTRING]"
allowed-tools: mcp__unifi__unifi_get_sites, mcp__unifi__unifi_get_devices
---

# /unifi-devices

List the UniFi devices (access points, switches, gateways) adopted at a site.

## Usage

`/unifi-devices [--site SITE_ID] [--type ap|switch|gateway] [--filter SUBSTRING]`

Arguments:

- `--site SITE_ID`: optional site ID to scope the query. Defaults to `default`. Validated against `mcp__unifi__unifi_get_sites`.
- `--type ap|switch|gateway`: optional device-type filter. Accepts the substring `ap` (matches type containing "ap"), `switch` (matches "switch"), or `gateway`. The filter runs client-side.
- `--filter SUBSTRING`: optional case-insensitive substring matched against MAC, name, model, or IP. The filter runs client-side after the tool returns.

## Workflow

1. Call `mcp__unifi__unifi_get_sites` to resolve the default site if `--site` is not supplied.
2. Call `mcp__unifi__unifi_get_devices` with the resolved `site_id` to fetch the full device list.
3. If `--type` is supplied, narrow the result by matching the device's `type` field.
4. If `--filter SUBSTRING` is supplied, narrow the result to entries where any of `mac`, `name`, `model`, or `ip` contains the substring (case-insensitive).
5. Report: total count, filtered count, and a table of MAC, name, model, IP, firmware version, and state (online/offline/isolated).
6. If the result is empty, report that explicitly and suggest verifying the site ID.

## Example

`/unifi-devices --type ap` — every access point in the `default` site.

`/unifi-devices --site branch-office --filter "u6-"` — devices whose model contains "u6-".
