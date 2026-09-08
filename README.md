# Super Productivity — Home Assistant integration

Pulls task, time-tracking and Focus Mode data from a running
[Super Productivity](https://super-productivity.com) desktop app through its
**Local REST API**, and lets you start, stop, create and archive tasks from
Home Assistant.

`local_polling` — Home Assistant polls the API every 30 seconds.

## Requirements

- Super Productivity **desktop** app (the Local REST API is desktop only).
- In Super Productivity: **Settings → Misc → enable the Local REST API**, then
  copy the **Access Token** shown there.
- The API listens on `127.0.0.1:3876` and only accepts loopback requests. If
  Home Assistant runs on a **different machine**, this integration still sends a
  loopback `Host` header so the request is accepted — you only need network
  reachability to the port. Point the `Host` field at the machine's LAN IP.

## Install

### HACS (custom repository)

1. HACS → ⋮ → **Custom repositories**.
2. Add `https://github.com/BigWebstas/super-productivity-hass`, category
   **Integration**.
3. Install **Super Productivity**, then restart Home Assistant.

### Manual

Copy `custom_components/super_productivity` into your HA `config/custom_components`
directory and restart.

## Configure

**Settings → Devices & services → Add integration → Super Productivity.**

| Field | Default | Notes |
|-------|---------|-------|
| Host | `127.0.0.1` | Machine running Super Productivity |
| Port | `3876` | Fixed by the app |
| Access token | – | Settings → Misc → Access Token |

If you regenerate the token in Super Productivity, Home Assistant raises a
re-auth prompt — paste the new one.

The poll interval (default 30 s, range 5–3600 s) is under the integration's
**Configure** button.

## Entities

| Entity | Type | Meaning |
|--------|------|---------|
| `sensor.super_productivity_current_task` | sensor | Title of the tracked task, `None` if none. Attributes: id, project, tags, time spent/estimate |
| `sensor.super_productivity_task_count` | sensor | Total active tasks |
| `sensor.super_productivity_tasks_today_open` | sensor | Today's tasks not done. Attribute: `titles` |
| `sensor.super_productivity_tasks_today_done` | sensor | Today's tasks done |
| `sensor.super_productivity_tasks_today_total` | sensor | Today's tasks total |
| `sensor.super_productivity_time_spent_today` | sensor | Minutes tracked today across today's tasks |
| `sensor.super_productivity_time_estimated_today` | sensor | Sum of today's task estimates, minutes |
| `sensor.super_productivity_focus_mode` | sensor | `Flowtime` / `Pomodoro` / `Countdown` |
| `sensor.super_productivity_focus_time_remaining` | sensor | Seconds left on the Focus timer |
| `binary_sensor.super_productivity_tracking` | binary_sensor | On when a task is current |
| `binary_sensor.super_productivity_focus_running` | binary_sensor | On when the Focus timer is running |
| `button.super_productivity_stop_tracking` | button | Stops time tracking |

## Services

| Service | Fields |
|---------|--------|
| `super_productivity.start_task` | `task_id` |
| `super_productivity.stop_task` | – |
| `super_productivity.create_task` | `title`, optional `project_id`, `parent_id`, `tag_ids`, `notes`, `time_estimate` (ms). Returns the created task |
| `super_productivity.archive_task` | `task_id` |

All services take an optional `config_entry_id` when more than one instance is
configured.

Task IDs come from the `task_id` / `project_id` attributes on the sensors, or
from `GET http://127.0.0.1:3876/tasks` directly.

## Limitations

- The API has no time-series/stats endpoint. "Time spent today" is summed from
  each of today's tasks using Home Assistant's local date as the day key, so it
  can be briefly off around midnight or if you use a custom start-of-day.
- Default read cadence is 30 s (adjustable in options).

## Disclaimer

Not affiliated with Super Productivity.
