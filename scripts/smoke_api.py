#!/usr/bin/env python3
"""Simple smoke test runner for GraphTools FastAPI endpoints."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import sys
import traceback
from typing import Callable
import urllib.error
import urllib.parse
import urllib.request


def fetch_json(url: str, timeout: float) -> tuple[object, int, str]:
    req = urllib.request.Request(url=url, method="GET")
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        body = resp.read().decode("utf-8")
        if resp.status != 200:
            raise RuntimeError(f"Expected 200, got {resp.status} for {url}")
        try:
            payload = json.loads(body)
        except json.JSONDecodeError as exc:
            raise RuntimeError(f"Invalid JSON from {url}: {exc}") from exc
        return payload, resp.status, body


def post_json(url: str, timeout: float, body: dict | None = None) -> tuple[object, int, str]:
    payload = json.dumps(body or {}).encode("utf-8")
    req = urllib.request.Request(
        url=url,
        method="POST",
        data=payload,
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        raw_body = resp.read().decode("utf-8")
        if resp.status != 200:
            raise RuntimeError(f"Expected 200, got {resp.status} for {url}")
        try:
            parsed = json.loads(raw_body)
        except json.JSONDecodeError as exc:
            raise RuntimeError(f"Invalid JSON from {url}: {exc}") from exc
        return parsed, resp.status, raw_body


def assert_init_payload(payload: object) -> None:
    if not isinstance(payload, dict):
        raise AssertionError(f"init: payload must be object: {payload}")
    data = payload.get("data")
    cluster = payload.get("cluster")
    if not isinstance(data, dict):
        raise AssertionError(f"init: data must be object: {payload}")
    if not isinstance(cluster, dict):
        raise AssertionError(f"init: cluster must be object: {payload}")
    loaded = data.get("loaded")
    if not isinstance(loaded, bool):
        raise AssertionError(f"init: data.loaded must be bool: {payload}")


def assert_scatter_payload(mode: str, payload: object) -> None:
    if not isinstance(payload, list):
        raise AssertionError(f"scatter({mode}): payload must be array")
    if len(payload) == 0:
        raise AssertionError(f"scatter({mode}): empty array")

    first = payload[0]
    if not isinstance(first, dict):
        raise AssertionError(f"scatter({mode}): first item must be object: {first}")
    if not isinstance(first.get("id"), str):
        raise AssertionError(f"scatter({mode}): id must be string: {first}")
    if not isinstance(first.get("x"), (int, float)):
        raise AssertionError(f"scatter({mode}): x must be number: {first}")
    if not isinstance(first.get("y"), (int, float)):
        raise AssertionError(f"scatter({mode}): y must be number: {first}")


def assert_hierarchy_payload(mode: str, payload: object) -> None:
    if not isinstance(payload, dict):
        raise AssertionError(f"hierarchy({mode}): payload must be object: {payload}")
    if not isinstance(payload.get("source"), str):
        raise AssertionError(f"hierarchy({mode}): source must be string: {payload}")
    if not isinstance(payload.get("raw"), str):
        raise AssertionError(f"hierarchy({mode}): raw must be string: {payload}")


def assert_dump_payload(payload: object) -> None:
    if not isinstance(payload, dict):
        raise AssertionError(f"dump: payload must be object: {payload}")
    tables = payload.get("tables")
    recent_jobs = payload.get("recent_jobs")
    if not isinstance(tables, dict):
        raise AssertionError(f"dump: tables must be object: {payload}")
    if not isinstance(recent_jobs, list):
        raise AssertionError(f"dump: recent_jobs must be list: {payload}")


def _write_failure_report(
    *,
    log_dir: str,
    base_url: str,
    timeout: float,
    records: list[dict],
    error: Exception,
) -> str:
    Path(log_dir).mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    out_path = Path(log_dir) / f"smoke_failure_{stamp}.json"

    report = {
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "base_url": base_url,
        "timeout_seconds": timeout,
        "error_type": type(error).__name__,
        "error_message": str(error),
        "traceback": traceback.format_exc(),
        "records": records,
    }

    out_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    return str(out_path)


def _run_endpoint(
    *,
    path: str,
    base_url: str,
    timeout: float,
    records: list[dict],
    validator: Callable[[dict], None],
    success_message: Callable[[dict], str],
) -> None:
    url = f"{base_url}{path}"
    try:
        payload, status_code, _raw_body = fetch_json(url, timeout)
        validator(payload)
        records.append(
            {
                "endpoint": path,
                "url": url,
                "ok": True,
                "status_code": status_code,
                "response": payload,
            }
        )
        print(success_message(payload))
    except urllib.error.HTTPError as exc:
        details = exc.read().decode("utf-8", errors="replace")
        records.append(
            {
                "endpoint": path,
                "url": url,
                "ok": False,
                "status_code": exc.code,
                "error": f"HTTPError: {exc}",
                "response_text": details,
            }
        )
        raise RuntimeError(f"HTTP {exc.code} on {url} body={details}") from exc
    except urllib.error.URLError as exc:
        records.append(
            {
                "endpoint": path,
                "url": url,
                "ok": False,
                "status_code": None,
                "error": f"URLError: {exc}",
            }
        )
        raise RuntimeError(f"connection error on {url}: {exc}") from exc
    except Exception as exc:
        records.append(
            {
                "endpoint": path,
                "url": url,
                "ok": False,
                "status_code": None,
                "error": f"{type(exc).__name__}: {exc}",
            }
        )
        raise


def _run_post_endpoint(
    *,
    path: str,
    base_url: str,
    timeout: float,
    records: list[dict],
    validator: Callable[[object], None],
    success_message: Callable[[object], str],
    body: dict | None = None,
) -> None:
    url = f"{base_url}{path}"
    try:
        payload, status_code, _raw_body = post_json(url, timeout, body)
        validator(payload)
        records.append(
            {
                "endpoint": path,
                "method": "POST",
                "url": url,
                "ok": True,
                "status_code": status_code,
                "response": payload,
            }
        )
        print(success_message(payload))
    except urllib.error.HTTPError as exc:
        details = exc.read().decode("utf-8", errors="replace")
        records.append(
            {
                "endpoint": path,
                "method": "POST",
                "url": url,
                "ok": False,
                "status_code": exc.code,
                "error": f"HTTPError: {exc}",
                "response_text": details,
            }
        )
        raise RuntimeError(f"HTTP {exc.code} on {url} body={details}") from exc
    except urllib.error.URLError as exc:
        records.append(
            {
                "endpoint": path,
                "method": "POST",
                "url": url,
                "ok": False,
                "status_code": None,
                "error": f"URLError: {exc}",
            }
        )
        raise RuntimeError(f"connection error on {url}: {exc}") from exc
    except Exception:
        raise


def run(base_url: str, timeout: float) -> list[dict]:
    records: list[dict] = []

    print(f"Base URL: {base_url}")

    _run_post_endpoint(
        path="/init",
        base_url=base_url,
        timeout=timeout,
        records=records,
        validator=assert_init_payload,
        success_message=lambda payload: (
            f"PASS /init loaded={payload['data'].get('loaded')} rows={payload['data'].get('rows', 0)}"
        ),
    )

    for mode in ("raw", "cluster", "dense"):
        query = urllib.parse.urlencode({"mode": mode})
        path = f"/scatter?{query}"
        _run_endpoint(
            path=path,
            base_url=base_url,
            timeout=timeout,
            records=records,
            validator=lambda payload, current_mode=mode: assert_scatter_payload(
                current_mode, payload
            ),
            success_message=lambda payload, current_mode=mode: (
                f"PASS /scatter mode={current_mode} count={len(payload)}"
            ),
        )

    for mode in ("cluster", "dense"):
        query = urllib.parse.urlencode({"mode": mode})
        path = f"/hierarchy?{query}"
        _run_endpoint(
            path=path,
            base_url=base_url,
            timeout=timeout,
            records=records,
            validator=lambda payload, current_mode=mode: assert_hierarchy_payload(
                current_mode, payload
            ),
            success_message=lambda payload, current_mode=mode: (
                f"PASS /hierarchy mode={current_mode} source={payload['source']}"
            ),
        )

    _run_endpoint(
        path="/dump",
        base_url=base_url,
        timeout=timeout,
        records=records,
        validator=assert_dump_payload,
        success_message=lambda payload: (
            f"PASS /dump recent_jobs={len(payload['recent_jobs'])} tables={len(payload['tables'])}"
        ),
    )

    return records


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run GraphTools API smoke tests")
    parser.add_argument(
        "--base-url",
        default="http://127.0.0.1:8005",
        help="FastAPI base URL",
    )
    parser.add_argument(
        "--timeout",
        type=float,
        default=15.0,
        help="Per-request timeout in seconds",
    )
    parser.add_argument(
        "--log-dir",
        default="logs/smoke",
        help="Directory to write failure report JSON",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    base_url = args.base_url.rstrip("/")
    records: list[dict] = []

    try:
        records = run(base_url, args.timeout)
    except Exception as exc:
        report_path = _write_failure_report(
            log_dir=args.log_dir,
            base_url=base_url,
            timeout=args.timeout,
            records=records,
            error=exc,
        )
        print(f"SMOKE TEST FAILED: {exc}", file=sys.stderr)
        print(f"Failure report written: {report_path}", file=sys.stderr)
        return 1

    print("SMOKE TEST PASSED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
