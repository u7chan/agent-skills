#!/usr/bin/env python3
"""Diagnose Chrome remote debugging reachability from WSL."""

from __future__ import annotations

import argparse
import json
import os
import socket
import struct
import sys
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass


DEFAULT_PORT = 9333


@dataclass(frozen=True)
class Candidate:
    url: str
    source: str


@dataclass(frozen=True)
class Result:
    candidate: Candidate
    ok: bool
    error: str | None = None
    data: dict | None = None


def normalize_base_url(value: str, port: int) -> str:
    value = value.strip()
    if not value:
        raise ValueError("empty URL")

    if "://" not in value:
        value = f"http://{value}"

    parsed = urllib.parse.urlparse(value)
    if parsed.scheme not in {"http", "https"}:
        raise ValueError(f"unsupported scheme: {parsed.scheme}")
    if not parsed.hostname:
        raise ValueError("missing host")

    hostname = parsed.hostname
    if ":" in hostname and not hostname.startswith("["):
        hostname = f"[{hostname}]"

    netloc = hostname
    if parsed.port:
        netloc = f"{netloc}:{parsed.port}"
    elif port:
        netloc = f"{netloc}:{port}"

    return urllib.parse.urlunparse((parsed.scheme, netloc, "", "", "", "")).rstrip("/")


def read_resolv_nameservers() -> list[str]:
    nameservers: list[str] = []
    try:
        with open("/etc/resolv.conf", "r", encoding="utf-8") as resolv:
            for line in resolv:
                parts = line.split()
                if len(parts) >= 2 and parts[0] == "nameserver":
                    nameservers.append(parts[1])
    except OSError:
        pass
    return nameservers


def read_default_gateways() -> list[str]:
    gateways: list[str] = []
    try:
        with open("/proc/net/route", "r", encoding="utf-8") as routes:
            next(routes, None)
            for line in routes:
                parts = line.split()
                if len(parts) < 3 or parts[1] != "00000000":
                    continue
                try:
                    gateway = socket.inet_ntoa(struct.pack("<L", int(parts[2], 16)))
                except (OSError, ValueError):
                    continue
                if gateway != "0.0.0.0":
                    gateways.append(gateway)
    except OSError:
        pass
    return gateways


def build_candidates(port: int, explicit: list[str]) -> list[Candidate]:
    raw: list[tuple[str, str]] = []

    env_url = os.environ.get("CHROME_DEBUG_URL")
    if env_url:
        raw.append((env_url, "CHROME_DEBUG_URL"))

    for item in explicit:
        raw.append((item, "--candidate"))

    raw.extend(
        [
            (f"http://127.0.0.1:{port}", "loopback IPv4"),
            (f"http://localhost:{port}", "localhost"),
            (f"http://host.docker.internal:{port}", "host.docker.internal"),
        ]
    )

    for nameserver in read_resolv_nameservers():
        raw.append((f"http://{nameserver}:{port}", "/etc/resolv.conf nameserver"))

    for gateway in read_default_gateways():
        raw.append((f"http://{gateway}:{port}", "default gateway"))

    candidates: list[Candidate] = []
    seen: set[str] = set()
    for value, source in raw:
        try:
            url = normalize_base_url(value, port)
        except ValueError as exc:
            candidates.append(Candidate(f"{value} (invalid: {exc})", source))
            continue
        if url not in seen:
            candidates.append(Candidate(url, source))
            seen.add(url)

    return candidates


def fetch_version(candidate: Candidate, timeout: float) -> Result:
    if " (invalid: " in candidate.url:
        return Result(candidate, ok=False, error="invalid candidate")

    endpoint = f"{candidate.url}/json/version"
    request = urllib.request.Request(endpoint, headers={"Accept": "application/json"})

    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            body = response.read().decode("utf-8")
            data = json.loads(body)
    except urllib.error.HTTPError as exc:
        return Result(candidate, ok=False, error=f"HTTP {exc.code}")
    except urllib.error.URLError as exc:
        return Result(candidate, ok=False, error=str(exc.reason))
    except socket.timeout:
        return Result(candidate, ok=False, error="timeout")
    except json.JSONDecodeError as exc:
        return Result(candidate, ok=False, error=f"invalid JSON: {exc}")
    except OSError as exc:
        return Result(candidate, ok=False, error=str(exc))

    websocket = data.get("webSocketDebuggerUrl")
    browser = data.get("Browser")
    if not browser or not websocket:
        return Result(
            candidate,
            ok=False,
            error="response missing Browser or webSocketDebuggerUrl",
            data=data,
        )

    return Result(candidate, ok=True, data=data)


def mcp_json(browser_url: str) -> str:
    config = {
        "mcpServers": {
            "chrome-devtools": {
                "command": "npx",
                "args": [
                    "chrome-devtools-mcp@latest",
                    f"--browserUrl={browser_url}",
                ],
            }
        }
    }
    return json.dumps(config, indent=2)


def print_failure_help(port: int) -> None:
    print()
    print("No reachable Chrome remote debugging endpoint was found.")
    print()
    print("Run this in Windows PowerShell to verify the tested endpoint on Windows:")
    print(f"  Invoke-RestMethod http://127.0.0.1:{port}/json/version")
    if port != DEFAULT_PORT:
        print()
        print("If this port is a portproxy listener, also verify Chrome's actual CDP port:")
        print(f"  Invoke-RestMethod http://127.0.0.1:{DEFAULT_PORT}/json/version")
    print()
    print("If PowerShell fails:")
    print("  - Start Chrome with --remote-debugging-port and a dedicated --user-data-dir.")
    print("  - Make sure the command did not get absorbed by an existing Chrome process.")
    print("  - If using portproxy, Chrome may simply be stopped behind the forwarding port.")
    print()
    print("If PowerShell succeeds but WSL fails:")
    print("  - Check WSL networking mode, Windows Firewall, and Chrome listen scope.")
    print("  - Avoid --remote-debugging-address=0.0.0.0 unless the exposure risk is understood.")


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Diagnose Chrome remote debugging reachability from WSL."
    )
    parser.add_argument("--port", type=int, default=DEFAULT_PORT, help="Chrome remote debugging port.")
    parser.add_argument(
        "--timeout",
        type=float,
        default=1.5,
        help="Per-candidate HTTP timeout in seconds.",
    )
    parser.add_argument(
        "--candidate",
        action="append",
        default=[],
        help="Additional browser URL candidate to try before built-in candidates.",
    )
    return parser.parse_args(argv)


def main(argv: list[str]) -> int:
    args = parse_args(argv)
    candidates = build_candidates(args.port, args.candidate)

    print("Checking Chrome remote debugging endpoints from WSL...")
    print()

    results = [fetch_version(candidate, args.timeout) for candidate in candidates]
    for result in results:
        status = "OK" if result.ok else "FAIL"
        detail = ""
        if result.error:
            detail = f" - {result.error}"
        print(f"[{status}] {result.candidate.url} ({result.candidate.source}){detail}")

    success = next((result for result in results if result.ok), None)
    if not success or not success.data:
        print_failure_help(args.port)
        return 1

    data = success.data
    browser_url = success.candidate.url
    print()
    print("Use this Chrome remote debugging URL:")
    print(f"  {browser_url}")
    print()
    print("Chrome details:")
    print(f"  Browser: {data.get('Browser')}")
    print(f"  webSocketDebuggerUrl: {data.get('webSocketDebuggerUrl')}")
    print()
    print("chrome-devtools-mcp argument:")
    print(f"  --browserUrl={browser_url}")
    print()
    print("MCP JSON example:")
    print(mcp_json(browser_url))

    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
