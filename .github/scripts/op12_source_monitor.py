#!/usr/bin/env python3
"""Monitor OnePlusOSS repositories for OnePlus 12 kernel source & manifest updates."""

from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any

ORG = "OnePlusOSS"
API_BASE = "https://api.github.com"

MANIFEST_REPO = f"{ORG}/kernel_manifest"
KNOWN_KERNEL_REPOS = (
    f"{ORG}/android_kernel_common_oneplus_sm8650",
    f"{ORG}/android_kernel_modules_and_devicetree_oneplus_sm8650",
    f"{ORG}/android_kernel_oneplus_sm8650",
)

REPO_DISCOVERY_RE = re.compile(r"(sm8650|oneplus[_-]?12|waffle)", re.I)
MANIFEST_BRANCH_RE = re.compile(r"(sm8650|oneplus[_-]?12|waffle)", re.I)
OP12_TOKEN_RE = re.compile(r"(oneplus[_-]?12|waffle)", re.I)
A17_HINT_RE = re.compile(r"(17\.0|_c_|_w\.xml|_c\.xml|6\.1\.15[7-9]|6\.1\.1[6-9]\d)", re.I)


def utc_now_iso() -> str:
    """Return the current UTC timestamp formatted cleanly."""
    return dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")


class GitHubClient:
    """Minimal authenticated GitHub REST API client using Python stdlib."""

    def __init__(self, token: str | None = None, timeout: int = 30, max_retries: int = 4) -> None:
        self.token = token or os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN") or ""
        self.timeout = timeout
        self.max_retries = max_retries

    def _headers(self, accept: str) -> dict[str, str]:
        headers = {
            "Accept": accept,
            "User-Agent": "OnePlus12-KernelSU-SUSFS-Monitor/1.0",
            "X-GitHub-Api-Version": "2022-11-28",
        }
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        return headers

    def request(self, url: str, accept: str = "application/vnd.github+json") -> tuple[bytes, dict[str, str]]:
        """Execute a GET request with retries on transient HTTP or network errors."""
        last_err: Exception | None = None
        for attempt in range(1, self.max_retries + 1):
            req = urllib.request.Request(url, headers=self._headers(accept))
            try:
                with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                    body = resp.read()
                    hdrs = {k.lower(): v for k, v in resp.headers.items()}
                    return body, hdrs
            except urllib.error.HTTPError as exc:
                last_err = exc
                if exc.code == 404:
                    raise
                retryable = exc.code in (429, 500, 502, 503, 504) or (
                    exc.code == 403 and exc.headers.get("x-ratelimit-remaining") == "0"
                )
                if not retryable or attempt == self.max_retries:
                    raise
                time.sleep(min(2**attempt, 16))
            except (urllib.error.URLError, TimeoutError) as exc:
                last_err = exc
                if attempt == self.max_retries:
                    raise
                time.sleep(min(2**attempt, 16))
        assert last_err is not None
        raise last_err

    def get_json(self, path_or_url: str) -> tuple[Any, dict[str, str]]:
        """Fetch and decode JSON from an API path or full URL."""
        url = path_or_url if path_or_url.startswith("http") else f"{API_BASE}/{path_or_url.lstrip('/')}"
        raw, hdrs = self.request(url)
        return json.loads(raw.decode("utf-8")), hdrs

    def get_paginated(self, path: str) -> list[Any]:
        """Fetch all pages of a GitHub REST list endpoint."""
        sep = "&" if "?" in path else "?"
        next_url: str | None = f"{API_BASE}/{path.lstrip('/')}{sep}per_page=100"
        items: list[Any] = []
        while next_url:
            data, hdrs = self.get_json(next_url)
            if isinstance(data, list):
                items.extend(data)
            next_url = _parse_next_link(hdrs.get("link", ""))
        return items

    def get_file_text(self, repo: str, ref: str, file_path: str) -> str | None:
        """Fetch raw UTF-8 file text via the GitHub Contents API, returning None on 404."""
        encoded_path = "/".join(urllib.parse.quote(part, safe="") for part in file_path.split("/"))
        encoded_ref = urllib.parse.quote(ref, safe="")
        url = f"{API_BASE}/repos/{repo}/contents/{encoded_path}?ref={encoded_ref}"
        try:
            raw, _ = self.request(url, accept="application/vnd.github.raw+json")
            return raw.decode("utf-8", errors="replace")
        except urllib.error.HTTPError as exc:
            if exc.code == 404:
                return None
            raise


def _parse_next_link(link_header: str) -> str | None:
    if not link_header:
        return None
    for part in link_header.split(","):
        sections = [s.strip() for s in part.split(";")]
        if len(sections) >= 2 and sections[1] == 'rel="next"' and sections[0].startswith("<") and sections[0].endswith(">"):
            return sections[0][1:-1]
    return None


def parse_makefile_version(makefile_text: str | None) -> str:
    """Extract VERSION.PATCHLEVEL.SUBLEVEL from a Linux kernel Makefile."""
    if not makefile_text:
        return "unknown"
    values: dict[str, str] = {}
    for line in makefile_text.splitlines():
        m = re.match(r"^\s*(VERSION|PATCHLEVEL|SUBLEVEL)\s*=\s*(\d+)\s*$", line)
        if m:
            values[m.group(1)] = m.group(2)
        if len(values) == 3:
            break
    if all(k in values for k in ("VERSION", "PATCHLEVEL", "SUBLEVEL")):
        return f"{values['VERSION']}.{values['PATCHLEVEL']}.{values['SUBLEVEL']}"
    return "unknown"


def parse_manifest_xml(xml_text: str | None) -> dict[str, str]:
    """Extract key SM8650 project revisions from a OnePlus kernel manifest XML."""
    revisions: dict[str, str] = {}
    if not xml_text:
        return revisions
    try:
        root = ET.fromstring(xml_text)
    except ET.ParseError:
        return revisions

    default_el = root.find("default")
    default_rev = default_el.attrib.get("revision", "") if default_el is not None else ""

    for proj in root.findall("project"):
        name = proj.attrib.get("name", "")
        rev = proj.attrib.get("revision") or default_rev
        if not rev:
            continue
        if "android_kernel_common" in name:
            revisions["common"] = rev
        elif "modules_and_devicetree" in name:
            revisions["modules"] = rev
        elif "android_kernel_oneplus" in name:
            revisions["oneplus"] = rev
    return dict(sorted(revisions.items()))


def commit_summary(message: str | None, limit: int = 90) -> str:
    """Normalize a commit message to a single compact summary line."""
    first_line = (message or "").splitlines()[0].strip() if message else ""
    first_line = re.sub(r"\s+", " ", first_line)
    if len(first_line) > limit:
        return first_line[: limit - 1].rstrip() + "…"
    return first_line or "-"


def discover_op12_repos(client: GitHubClient) -> list[str]:
    """Discover all OnePlusOSS repositories relevant to OnePlus 12 / SM8650."""
    repos = set(KNOWN_KERNEL_REPOS)
    repos.add(MANIFEST_REPO)
    try:
        org_repos = client.get_paginated(f"orgs/{ORG}/repos")
        for repo in org_repos:
            name = repo.get("name", "")
            full_name = repo.get("full_name", f"{ORG}/{name}")
            if name == "kernel_manifest" or REPO_DISCOVERY_RE.search(name):
                repos.add(full_name)
    except urllib.error.URLError as exc:
        print(f"Warning: repo discovery fallback to known repos ({exc})", file=sys.stderr)
    return sorted(repos)


def collect_op12_snapshot(client: GitHubClient) -> dict[str, Any]:
    """Collect the live OnePlus 12 state from OnePlusOSS."""
    tracked_repos = discover_op12_repos(client)
    manifests: dict[str, dict[str, Any]] = {}
    branches: dict[str, dict[str, Any]] = {}

    if MANIFEST_REPO in tracked_repos:
        manifest_branches = client.get_paginated(f"repos/{MANIFEST_REPO}/branches")
        for b in manifest_branches:
            bname = b.get("name", "")
            if not MANIFEST_BRANCH_RE.search(bname):
                continue
            ref_q = urllib.parse.quote(bname, safe="")
            entries, _ = client.get_json(f"repos/{MANIFEST_REPO}/contents?ref={ref_q}")
            if not isinstance(entries, list):
                continue
            for entry in entries:
                fname = entry.get("name", "")
                if entry.get("type") == "file" and OP12_TOKEN_RE.search(fname):
                    key = f"{bname}:{fname}"
                    xml_text = client.get_file_text(MANIFEST_REPO, bname, fname)
                    manifests[key] = {
                        "branch": bname,
                        "file": fname,
                        "blob_sha": entry.get("sha", ""),
                        "html_url": entry.get("html_url", ""),
                        "revisions": parse_manifest_xml(xml_text),
                    }

    for repo in tracked_repos:
        if repo == MANIFEST_REPO:
            continue
        is_dedicated_op12_repo = bool(OP12_TOKEN_RE.search(repo.split("/", 1)[-1]))
        repo_branches = client.get_paginated(f"repos/{repo}/branches")
        for b in repo_branches:
            bname = b.get("name", "")
            if not is_dedicated_op12_repo and not OP12_TOKEN_RE.search(bname):
                continue
            sha = b.get("commit", {}).get("sha", "")
            commit_obj, _ = client.get_json(f"repos/{repo}/commits/{sha}")
            commit_meta = commit_obj.get("commit", {})
            author_date = (
                commit_meta.get("committer", {}).get("date")
                or commit_meta.get("author", {}).get("date")
                or ""
            )
            entry: dict[str, Any] = {
                "repo": repo,
                "branch": bname,
                "commit_sha": sha,
                "commit_date": author_date,
                "commit_message": commit_summary(commit_meta.get("message")),
                "commit_url": commit_obj.get("html_url", f"https://github.com/{repo}/commit/{sha}"),
            }
            if "kernel_common" in repo:
                makefile = client.get_file_text(repo, bname, "Makefile")
                entry["kernel_version"] = parse_makefile_version(makefile)
            branches[f"{repo}@{bname}"] = entry

    return {
        "schema_version": 1,
        "org": ORG,
        "tracked_repos": sorted(tracked_repos),
        "manifests": dict(sorted(manifests.items())),
        "branches": dict(sorted(branches.items())),
    }


def compute_diff(old_state: dict[str, Any] | None, new_state: dict[str, Any]) -> dict[str, Any]:
    """Compare previous saved snapshot against the newly collected snapshot."""
    if old_state is None:
        return {
            "is_baseline": True,
            "has_changes": False,
            "has_a17_signal": _detect_a17_in_items(
                list(new_state.get("manifests", {}).keys()),
                list(new_state.get("branches", {}).values()),
            ),
            "added_repos": [],
            "removed_repos": [],
            "added_manifests": [],
            "updated_manifests": [],
            "removed_manifests": [],
            "added_branches": [],
            "updated_branches": [],
            "removed_branches": [],
        }

    old_repos = set(old_state.get("tracked_repos", []))
    new_repos = set(new_state.get("tracked_repos", []))

    old_manifests = old_state.get("manifests", {})
    new_manifests = new_state.get("manifests", {})

    old_branches = old_state.get("branches", {})
    new_branches = new_state.get("branches", {})

    added_manifests = [new_manifests[k] for k in sorted(new_manifests.keys() - old_manifests.keys())]
    removed_manifests = [old_manifests[k] for k in sorted(old_manifests.keys() - new_manifests.keys())]
    updated_manifests = []
    for k in sorted(old_manifests.keys() & new_manifests.keys()):
        if (
            old_manifests[k].get("blob_sha") != new_manifests[k].get("blob_sha")
            or old_manifests[k].get("revisions") != new_manifests[k].get("revisions")
        ):
            updated_manifests.append({"key": k, "old": old_manifests[k], "new": new_manifests[k]})

    added_branches = [new_branches[k] for k in sorted(new_branches.keys() - old_branches.keys())]
    removed_branches = [old_branches[k] for k in sorted(old_branches.keys() - new_branches.keys())]
    updated_branches = []
    for k in sorted(old_branches.keys() & new_branches.keys()):
        if (
            old_branches[k].get("commit_sha") != new_branches[k].get("commit_sha")
            or old_branches[k].get("kernel_version") != new_branches[k].get("kernel_version")
        ):
            updated_branches.append({"key": k, "old": old_branches[k], "new": new_branches[k]})

    added_repos = sorted(new_repos - old_repos)
    removed_repos = sorted(old_repos - new_repos)

    has_changes = any(
        [
            added_repos,
            removed_repos,
            added_manifests,
            updated_manifests,
            removed_manifests,
            added_branches,
            updated_branches,
            removed_branches,
        ]
    )

    changed_names = (
        added_repos
        + [m["file"] for m in added_manifests]
        + [u["new"]["file"] for u in updated_manifests]
    )
    changed_branches = added_branches + [u["new"] for u in updated_branches]

    return {
        "is_baseline": False,
        "has_changes": has_changes,
        "has_a17_signal": _detect_a17_in_items(changed_names, changed_branches),
        "added_repos": added_repos,
        "removed_repos": removed_repos,
        "added_manifests": added_manifests,
        "updated_manifests": updated_manifests,
        "removed_manifests": removed_manifests,
        "added_branches": added_branches,
        "updated_branches": updated_branches,
        "removed_branches": removed_branches,
    }


def _detect_a17_in_items(names: list[str], branch_objs: list[dict[str, Any]]) -> bool:
    for name in names:
        if A17_HINT_RE.search(name):
            return True
    for b in branch_objs:
        if A17_HINT_RE.search(b.get("branch", "")) or A17_HINT_RE.search(b.get("kernel_version", "")):
            return True
    return False


def _format_diff_sections(diff: dict[str, Any]) -> list[str]:
    lines: list[str] = []

    if diff["has_a17_signal"]:
        lines.extend(
            [
                "> [!IMPORTANT]",
                "> Potential **Android 17 (`17.0` / `_c_` / `6.1.157+`)** official source detected for OnePlus 12! "
                "Review `manifests/a17/oneplus_12_w.xml` to see if it can switch from the merged common tree to official `OnePlusOSS`.",
                "",
            ]
        )

    if diff["added_repos"]:
        lines.append("### 🆕 New Tracked Repositories")
        for r in diff["added_repos"]:
            lines.append(f"- [`{r}`](https://github.com/{r})")
        lines.append("")

    if diff["added_manifests"]:
        lines.append("### 📄 New Manifest Files")
        for m in diff["added_manifests"]:
            revs = ", ".join(f"`{k}={v}`" for k, v in m.get("revisions", {}).items()) or "none"
            lines.append(
                f"- [`{m['branch']}:{m['file']}`]({m['html_url']}) — blob `{m['blob_sha'][:10]}` ({revs})"
            )
        lines.append("")

    if diff["updated_manifests"]:
        lines.append("### 📝 Updated Manifest Files")
        for u in diff["updated_manifests"]:
            old_m, new_m = u["old"], u["new"]
            revs = ", ".join(f"`{k}={v}`" for k, v in new_m.get("revisions", {}).items()) or "none"
            lines.append(
                f"- [`{new_m['branch']}:{new_m['file']}`]({new_m['html_url']}) — "
                f"`{old_m['blob_sha'][:10]}` → `{new_m['blob_sha'][:10]}` ({revs})"
            )
        lines.append("")

    if diff["added_branches"]:
        lines.append("### 🌱 New OnePlus 12 Branches")
        for b in diff["added_branches"]:
            kver = f" (`{b['kernel_version']}`)" if b.get("kernel_version") else ""
            lines.append(
                f"- [`{b['repo']}`](https://github.com/{b['repo']}/tree/{b['branch']}) branch `{b['branch']}`{kver} "
                f"at [`{b['commit_sha'][:10]}`]({b['commit_url']}) — _{b['commit_message']}_"
            )
        lines.append("")

    if diff["updated_branches"]:
        lines.append("### 🔄 Updated OnePlus 12 Branches")
        for u in diff["updated_branches"]:
            old_b, new_b = u["old"], u["new"]
            ver_note = ""
            if old_b.get("kernel_version") or new_b.get("kernel_version"):
                ver_note = f" (`{old_b.get('kernel_version', '?')}` → `{new_b.get('kernel_version', '?')}`)"
            lines.append(
                f"- `{new_b['repo']}` `{new_b['branch']}`{ver_note}: "
                f"[`{old_b['commit_sha'][:10]}`...`{new_b['commit_sha'][:10]}`]"
                f"(https://github.com/{new_b['repo']}/compare/{old_b['commit_sha']}...{new_b['commit_sha']}) "
                f"— _{new_b['commit_message']}_"
            )
        lines.append("")

    if diff["removed_repos"] or diff["removed_manifests"] or diff["removed_branches"]:
        lines.append("### 🗑️ Removed Items")
        for r in diff["removed_repos"]:
            lines.append(f"- Repo removed: `{r}`")
        for m in diff["removed_manifests"]:
            lines.append(f"- Manifest removed: `{m['branch']}:{m['file']}`")
        for b in diff["removed_branches"]:
            lines.append(f"- Branch removed: `{b['repo']}` `{b['branch']}`")
        lines.append("")

    return lines


def _format_snapshot_tables(state: dict[str, Any]) -> list[str]:
    lines: list[str] = [
        "### 📄 Tracked OnePlus 12 Manifests (`OnePlusOSS/kernel_manifest`)",
        "",
        "| Branch | Manifest | Blob SHA | Key Revisions |",
        "|---|---|---|---|",
    ]
    for m in state.get("manifests", {}).values():
        revs = ", ".join(f"`{k}: {v}`" for k, v in m.get("revisions", {}).items()) or "-"
        file_link = f"[{m['file']}]({m['html_url']})" if m.get("html_url") else f"`{m['file']}`"
        lines.append(f"| `{m['branch']}` | {file_link} | `{m['blob_sha'][:10]}` | {revs} |")

    lines.extend(
        [
            "",
            "### 🌿 Tracked OnePlus 12 Kernel Branches",
            "",
            "| Repository | Branch | Kernel | Latest Commit | Date (UTC) | Message |",
            "|---|---|---|---|---|---|",
        ]
    )
    for b in state.get("branches", {}).values():
        short_repo = b["repo"].split("/", 1)[-1]
        kver = f"`{b['kernel_version']}`" if b.get("kernel_version") else "-"
        sha_link = f"[`{b['commit_sha'][:10]}`]({b['commit_url']})"
        cdate = (b.get("commit_date") or "").replace("T", " ").replace("Z", "")
        msg = b.get("commit_message", "-").replace("|", "\\|")
        lines.append(
            f"| `{short_repo}` | `{b['branch']}` | {kver} | {sha_link} | `{cdate or '-'}` | {msg} |"
        )
    lines.append("")
    return lines


def render_step_summary(state: dict[str, Any], diff: dict[str, Any], checked_at: str) -> str:
    """Render Markdown summary for $GITHUB_STEP_SUMMARY."""
    if diff["is_baseline"]:
        status_text = "🟢 Baseline Initialized"
    elif diff["has_changes"]:
        status_text = "🔔 Upstream OnePlus 12 Source Updates Detected"
    else:
        status_text = "✅ No Upstream Changes Detected"

    lines = [
        "## 🔍 OnePlus 12 Official Source Monitor (`OnePlusOSS`)",
        "",
        f"**Status:** {status_text}  ",
        f"**Checked At:** `{checked_at}`  ",
        f"**Tracked Manifests:** `{len(state.get('manifests', {}))}` | **Tracked Branches:** `{len(state.get('branches', {}))}`",
        "",
    ]
    if diff["has_changes"]:
        lines.extend(_format_diff_sections(diff))
    lines.extend(_format_snapshot_tables(state))
    return "\n".join(lines)


def render_issue_body(state: dict[str, Any], diff: dict[str, Any], checked_at: str, run_url: str) -> str:
    """Render GitHub Issue body when upstream changes occur or forced."""
    lines = [
        "## 🔔 OnePlus 12 Upstream Kernel Source Update (`OnePlusOSS`)",
        "",
        f"**Detected At:** `{checked_at}`  ",
    ]
    if run_url:
        lines.append(f"**Monitor Run:** {run_url}")
    lines.append("")

    if diff["has_changes"]:
        lines.extend(_format_diff_sections(diff))
    else:
        lines.extend(["_Baseline snapshot report triggered manually._", ""])

    lines.extend(_format_snapshot_tables(state))
    lines.extend(
        [
            "---",
            "*Generated automatically by `op12-source-monitor.yml`.*",
        ]
    )
    return "\n".join(lines)


def render_state_readme(state: dict[str, Any], checked_at: str) -> str:
    """Render README.md persisted alongside op12_source_state.json on monitor-state."""
    lines = [
        "# OnePlus 12 (`OnePlusOSS`) Source Monitor State",
        "",
        f"Last state update: `{checked_at}`",
        "",
    ]
    lines.extend(_format_snapshot_tables(state))
    return "\n".join(lines)


def build_issue_title(diff: dict[str, Any]) -> str:
    """Generate a concise issue title describing detected changes."""
    today = dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%d")
    if diff.get("is_baseline"):
        return f"[OP12 Source Monitor] Baseline snapshot ({today})"
    if diff.get("has_a17_signal"):
        return f"[OP12 Source Update] Potential Android 17 / 6.1.157+ source on OnePlusOSS ({today})"
    return f"[OP12 Source Update] New OnePlusOSS OnePlus 12 changes ({today})"


def changed_item_count(diff: dict[str, Any]) -> int:
    """Count total changed items across all categories."""
    return sum(
        len(diff[key])
        for key in (
            "added_repos",
            "removed_repos",
            "added_manifests",
            "updated_manifests",
            "removed_manifests",
            "added_branches",
            "updated_branches",
            "removed_branches",
        )
    )


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--state-file", required=True, help="Path to op12_source_state.json")
    parser.add_argument("--state-readme", help="Optional path to write state README.md")
    parser.add_argument("--summary-file", help="Path to write Markdown summary report")
    parser.add_argument("--issue-file", help="Path to write GitHub Issue body if changes/forced")
    parser.add_argument("--github-output", help="Path to $GITHUB_OUTPUT file")
    parser.add_argument("--force-issue", action="store_true", help="Write issue body even on baseline/no-change")
    parser.add_argument("--dry-run", action="store_true", help="Do not update --state-file or --state-readme")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    state_path = Path(args.state_file)

    old_state: dict[str, Any] | None = None
    if state_path.exists():
        old_state = json.loads(state_path.read_text(encoding="utf-8"))

    client = GitHubClient()
    new_state = collect_op12_snapshot(client)
    diff = compute_diff(old_state, new_state)
    checked_at = utc_now_iso()

    should_persist = diff["is_baseline"] or diff["has_changes"]
    if should_persist and not args.dry_run:
        state_path.parent.mkdir(parents=True, exist_ok=True)
        state_path.write_text(json.dumps(new_state, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        if args.state_readme:
            Path(args.state_readme).write_text(render_state_readme(new_state, checked_at), encoding="utf-8")

    summary_md = render_step_summary(new_state, diff, checked_at)
    if args.summary_file:
        Path(args.summary_file).write_text(summary_md, encoding="utf-8")
    else:
        print(summary_md)

    need_issue = diff["has_changes"] or args.force_issue
    issue_title = build_issue_title(diff)
    if args.issue_file and need_issue:
        server = os.environ.get("GITHUB_SERVER_URL", "https://github.com")
        repo = os.environ.get("GITHUB_REPOSITORY", "")
        run_id = os.environ.get("GITHUB_RUN_ID", "")
        run_url = f"{server}/{repo}/actions/runs/{run_id}" if repo and run_id else ""
        issue_md = render_issue_body(new_state, diff, checked_at, run_url)
        Path(args.issue_file).write_text(issue_md, encoding="utf-8")

    if args.github_output:
        lines = [
            f"is_baseline={'true' if diff['is_baseline'] else 'false'}",
            f"has_changes={'true' if diff['has_changes'] else 'false'}",
            f"state_updated={'true' if (should_persist and not args.dry_run) else 'false'}",
            f"need_issue={'true' if need_issue else 'false'}",
            f"changed_count={changed_item_count(diff)}",
            f"issue_title={issue_title}",
        ]
        with Path(args.github_output).open("a", encoding="utf-8") as fh:
            fh.write("\n".join(lines) + "\n")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())

