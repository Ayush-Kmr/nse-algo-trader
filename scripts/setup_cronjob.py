#!/usr/bin/env python3
"""Create the cron-job.org jobs that trigger the workflows, because GitHub's own schedule is unreliable.

    python3 scripts/setup_cronjob.py

Prompts for a cron-job.org API key and a GitHub fine-grained token (this repo, Actions: read and
write). Neither is saved here; the GitHub token is stored in the jobs at cron-job.org, which is how
they authenticate. Safe to run again: jobs that already exist are skipped, so to rotate the token,
delete the jobs in the console and rerun.
"""
from __future__ import annotations

import getpass
import json
import sys
import time
import urllib.error
import urllib.request

REPO = "Ayush-Kmr/nse-algo-trader"
API = "https://api.cron-job.org"
UA = "nse-algo-trader-setup"
EVERY_5 = list(range(2, 58, 5))  # :02, :07 ... :57

# Mon-Fri IST: ticks 09:32-15:27, end of day 15:45. Holidays run and exit at once.
JOBS = [
    ("nse tick 09:32-09:57", "paper-trade.yml", [9], [m for m in EVERY_5 if m >= 32]),
    ("nse tick 10:02-14:57", "paper-trade.yml", [10, 11, 12, 13, 14], EVERY_5),
    ("nse tick 15:02-15:27", "paper-trade.yml", [15], [m for m in EVERY_5 if m <= 27]),
    ("nse end of day 15:45", "eod.yml", [15], [45]),
]


def call(method: str, url: str, headers: dict, body=None) -> dict:
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(url, data=data, method=method,
                                 headers=dict(headers, **{"Content-Type": "application/json", "User-Agent": UA}))
    with urllib.request.urlopen(req, timeout=20) as r:
        raw = r.read().decode("utf-8")
    return json.loads(raw) if raw else {}


def job_body(title: str, workflow: str, hours: list, minutes: list, token: str) -> dict:
    return {"job": {
        "title": title,
        "enabled": True,
        "saveResponses": True,
        "url": "https://api.github.com/repos/%s/actions/workflows/%s/dispatches" % (REPO, workflow),
        "requestMethod": 1,  # POST
        "extendedData": {
            "headers": {"Authorization": "Bearer " + token, "Accept": "application/vnd.github+json",
                        "X-GitHub-Api-Version": "2022-11-28", "User-Agent": UA},
            "body": json.dumps({"ref": "main"}),
        },
        "schedule": {"timezone": "Asia/Kolkata", "expiresAt": 0, "hours": hours, "minutes": minutes,
                     "mdays": [-1], "months": [-1], "wdays": [1, 2, 3, 4, 5]},
        "notification": {"onFailure": True, "onFailureCount": 2, "onSuccess": True, "onDisable": True},
    }}


def main() -> int:
    key = getpass.getpass("cron-job.org API key: ").strip()
    token = getpass.getpass("GitHub fine-grained token: ").strip()
    cron = {"Authorization": "Bearer " + key}
    try:
        call("GET", "https://api.github.com/repos/%s/actions/workflows/paper-trade.yml" % REPO,
             {"Authorization": "Bearer " + token, "Accept": "application/vnd.github+json"})
        existing = {j.get("title") for j in call("GET", API + "/jobs", cron).get("jobs", [])}
        for title, workflow, hours, minutes in JOBS:
            if title in existing:
                print("exists  %s" % title)
                continue
            res = call("PUT", API + "/jobs", cron, job_body(title, workflow, hours, minutes, token))
            print("created %s (job %s)" % (title, res.get("jobId")))
            time.sleep(1.5)  # cron-job.org allows one create per second
    except urllib.error.HTTPError as e:
        print("failed: HTTP %s from %s" % (e.code, e.url.split("?")[0]))
        return 1
    print("done. cron-job.org will email you if these calls start failing.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
