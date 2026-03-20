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


def fetch_json(url: str, timeout: float) -> tuple[dict, int, str]:
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


def assert_pipeline_payload(name: str, payload: dict) -> None:
    if payload.get("status") != "ok":
        raise AssertionError(f"{name}: status is not ok: {payload}")
    count = payload.get("count")
    if not isinstance(count, int) or count < 0:
        raise AssertionError(f"{name}: invalid count: {payload}")


def assert_scatter_payload(mode: str, payload: dict) -> None:
    count = payload.get("count")
    data = payload.get("data")
    if not isinstance(count, int) or count < 0:
        raise AssertionError(f"scatter({mode}): invalid count: {payload}")
    if not isinstance(data, list):
        raise AssertionError(f"scatter({mode}): data must be list: {payload}")
    if count != len(data):
        raise AssertionError(
            f"scatter({mode}): count mismatch count={count} len(data)={len(data)}"
        )


def assert_jobs_payload(payload: dict) -> None:
    count = payload.get("count")
    jobs = payload.get("jobs")
    if not isinstance(count, int) or count < 0:
        raise AssertionError(f"jobs: invalid count: {payload}")
    if not isinstance(jobs, list):
        raise AssertionError(f"jobs: jobs must be list: {payload}")
    if count != len(jobs):
        raise AssertionError(f"jobs: count mismatch count={count} len(jobs)={len(jobs)}")


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


def run(base_url: str, timeout: float) -> list[dict]:
    pipeline_paths = ["/raw", "/random", "/cluster"]
    records: list[dict] = []

    print(f"Base URL: {base_url}")

    for path in pipeline_paths:
        _run_endpoint(
            path=path,
            base_url=base_url,
            timeout=timeout,
            records=records,
            validator=lambda payload, name=path: assert_pipeline_payload(name, payload),
            success_message=lambda payload, name=path: f"PASS {name} count={payload['count']}",
        )

    for mode in ("raw", "random", "cluster"):
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
                f"PASS /scatter mode={current_mode} count={payload['count']}"
            ),
        )

    _run_endpoint(
        path="/jobs",
        base_url=base_url,
        timeout=timeout,
        records=records,
        validator=assert_jobs_payload,
        success_message=lambda payload: f"PASS /jobs count={payload['count']}",
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
