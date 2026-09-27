"""PHG HTML capture worker v2 (PHG-034) - drop-in for the Railway HTML screenshot worker.

Speaks the existing menu-render-worker-api protocol (no server change needed):
  POST ?action=claim_html                      -> {status:"job", page_id, source_url, target_width, jpeg_quality}
  POST ?action=complete_html&page_id&width&height   body = JPEG
  POST ?action=fail_html                       body = {"page_id", "error"}
Headers: x-worker-token (required), x-worker-id (identity for the claim breaker).

Environment:
  PHG_WORKER_API_URL  https://<project>.supabase.co/functions/v1/menu-render-worker-api
  PHG_WORKER_TOKEN    same value as internal_secrets.menu_html_worker_token (never logged)
  PHG_WORKER_ID       optional, defaults to the hostname
  PHG_IDLE_SECONDS    optional poll delay when the queue is empty (default 15)
  PHG_CHROMIUM_PATH   optional Chromium binary (default: the one bundled with Playwright)
  PHG_AUTH            "token" (default, x-worker-token) or "github-oidc" (GitHub Actions: x-gh-oidc, for
                      menu-capture-v2-api; needs `permissions: id-token: write`, no stored secret)
  PHG_MAX_JOBS        optional; stop after this many pages (0 = no limit)
  PHG_EXIT_WHEN_EMPTY optional; "1" = exit when the queue is empty (Actions runs)

One page at a time, a fresh browser context per page, and the browser is restarted after a crash
so a dead browser never burns the queue (the API also has a breaker for that).
"""
from __future__ import annotations

import asyncio
import json
import os
import socket
import sys
import time
import urllib.error
import urllib.request

from playwright.async_api import async_playwright

from capture import capture

API = os.environ.get("PHG_WORKER_API_URL", "").rstrip("?")
TOKEN = os.environ.get("PHG_WORKER_TOKEN", "")
WORKER_ID = os.environ.get("PHG_WORKER_ID") or ("html-v2-" + socket.gethostname())
IDLE = float(os.environ.get("PHG_IDLE_SECONDS", "15"))
AUTH = os.environ.get("PHG_AUTH", "token")
MAX_JOBS = int(os.environ.get("PHG_MAX_JOBS", "0") or 0)
EXIT_WHEN_EMPTY = os.environ.get("PHG_EXIT_WHEN_EMPTY") == "1"
_oidc = {"tok": "", "at": 0.0}
UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) "
      "Chrome/128.0 Safari/537.36")


def _auth_headers() -> dict:
    if AUTH != "github-oidc":
        return {"x-worker-token": TOKEN}
    if not _oidc["tok"] or time.time() - _oidc["at"] > 240:  # GitHub OIDC tokens live ~5-10 min
        url = os.environ["ACTIONS_ID_TOKEN_REQUEST_URL"] + "&audience=phg-menu-capture-v2"
        r = urllib.request.Request(url, headers={"Authorization": "Bearer " + os.environ["ACTIONS_ID_TOKEN_REQUEST_TOKEN"]})
        with urllib.request.urlopen(r, timeout=30) as resp:
            _oidc["tok"], _oidc["at"] = json.loads(resp.read())["value"], time.time()
    return {"x-gh-oidc": _oidc["tok"]}


def _post(action: str, body: bytes = b"{}", ctype: str = "application/json", **q) -> dict:
    qs = "&".join([f"action={action}"] + [f"{k}={v}" for k, v in q.items()])
    req = urllib.request.Request(f"{API}?{qs}", data=body, method="POST", headers={
        **_auth_headers(), "x-worker-id": WORKER_ID, "content-type": ctype})
    try:
        with urllib.request.urlopen(req, timeout=120) as r:
            return json.loads(r.read() or b"{}")
    except urllib.error.HTTPError as e:
        try:
            return json.loads(e.read() or b"{}") | {"http_status": e.code}
        except Exception:
            return {"error": f"http {e.code}", "http_status": e.code}


async def run() -> None:
    if not API or (AUTH != "github-oidc" and not TOKEN):
        sys.exit("PHG_WORKER_API_URL and PHG_WORKER_TOKEN (or PHG_AUTH=github-oidc) are required")
    done = 0
    async with async_playwright() as p:
        browser = None
        while not MAX_JOBS or done < MAX_JOBS:
            if browser is None or not browser.is_connected():
                browser = await p.chromium.launch(executable_path=os.environ.get("PHG_CHROMIUM_PATH") or None,
                                                  args=["--no-sandbox", "--disable-dev-shm-usage"])
            job = await asyncio.to_thread(_post, "claim_html")
            if job.get("status") != "job":
                if job.get("http_status") == 401:
                    sys.exit("unauthorized: " + json.dumps(job))
                if EXIT_WHEN_EMPTY and job.get("status") == "empty":
                    print(json.dumps({"queue": "empty", "done": done}), flush=True)
                    return
                await asyncio.sleep(IDLE)
                continue
            pid = job["page_id"]
            done += 1
            ctx = None
            try:
                ctx = await browser.new_context(user_agent=UA, locale="en-US", ignore_https_errors=True)
                page = await ctx.new_page()
                cap = await asyncio.wait_for(
                    capture(page, job["source_url"], int(job.get("target_width") or 1400), int(job.get("jpeg_quality") or 85)),
                    timeout=180)
                res = await asyncio.to_thread(_post, "complete_html", cap.jpeg, "image/jpeg",
                                              page_id=pid, width=cap.width, height=cap.height)
                print(json.dumps({"page_id": pid, "status": res.get("status") or res.get("error"),
                                  "h": cap.height, "notes": cap.notes}), flush=True)
            except Exception as e:  # report and move on; the API decides backoff / quarantine
                msg = f"{type(e).__name__}: {e}"[:480]
                await asyncio.to_thread(_post, "fail_html", json.dumps({"page_id": pid, "error": msg}).encode())
                print(json.dumps({"page_id": pid, "failed": msg[:160]}), flush=True)
                if "Target crashed" in msg or "closed" in msg:
                    try:
                        await browser.close()
                    except Exception:
                        pass
                    browser = None
            finally:
                if ctx is not None:
                    try:
                        await ctx.close()
                    except Exception:
                        pass


if __name__ == "__main__":
    asyncio.run(run())
