#!/usr/bin/env python3
"""Probe the Super Productivity Local REST API and dump response shapes.

Usage:
    python3 scripts/probe_api.py <ACCESS_TOKEN> [host] [port]

Only reads. Nothing is created or modified.
"""

from __future__ import annotations

import json
import sys
import urllib.error
import urllib.request

token = sys.argv[1] if len(sys.argv) > 1 else ""
host = sys.argv[2] if len(sys.argv) > 2 else "127.0.0.1"
port = sys.argv[3] if len(sys.argv) > 3 else "3876"
base = f"http://{host}:{port}"


def get(path: str, auth: bool = True):
    req = urllib.request.Request(f"{base}{path}", method="GET")
    req.add_header("Host", f"127.0.0.1:{port}")
    if auth:
        req.add_header("Authorization", f"Bearer {token}")
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            return resp.status, json.load(resp)
    except urllib.error.HTTPError as err:
        return err.code, json.loads(err.read() or b"null")
    except Exception as err:  # noqa: BLE001
        return None, repr(err)


for path, auth in [
    ("/health", False),
    ("/status", True),
    ("/focus", True),
    ("/tasks?tagId=TODAY&includeDone=true", True),
    ("/projects", True),
    ("/tags", True),
]:
    status, body = get(path, auth)
    print(f"\n===== GET {path}  ->  {status} =====")
    print(json.dumps(body, indent=2, default=str)[:4000])
