#!/usr/bin/env python3
"""Generate a categorized research index from the authenticated user's public GitHub Lists.

The API is read-only. Generated files are written to this repository:
  README.md              index, methodology, snapshot metadata, and totals
  lists/<slug>.md        one table per public GitHub List

List membership is curated manually in GitHub. This script only renders that
curation into reproducible Markdown snapshots.
"""
from __future__ import annotations

from datetime import datetime, timezone
import json
from pathlib import Path
import re
import subprocess
import sys
import time

OUT = Path(__file__).resolve().parents[1]
LISTS_DIR = OUT / "lists"
VIEWS_DIR = OUT / "views"
SNAPSHOTS_DIR = OUT / "snapshots"


def gq(query: str) -> dict:
    """Run a GitHub GraphQL query, retry transient failures, then fail closed."""
    last_error = "unknown GraphQL failure"
    for attempt in range(1, 9):
        proc = subprocess.run(
            ["gh", "api", "graphql", "-f", f"query={query}"],
            text=True,
            capture_output=True,
        )
        if proc.returncode == 0:
            try:
                data = json.loads(proc.stdout)
            except json.JSONDecodeError as exc:
                last_error = f"invalid JSON: {exc}"
            else:
                if not data.get("errors"):
                    return data
                last_error = json.dumps(data["errors"])
        else:
            last_error = proc.stderr.strip() or f"gh exited {proc.returncode}"

        sys.stderr.write(
            f"GraphQL attempt {attempt}/8 failed: {last_error[:300]}\n"
        )
        time.sleep(6)

    raise RuntimeError(f"GitHub GraphQL failed after 8 attempts: {last_error}")


def slug(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")


def list_items(list_id: str) -> list[dict]:
    query = (
        'query($c:String){ node(id:%s){ ... on UserList { items(first:100, after:$c){ '
        'pageInfo{hasNextPage endCursor} nodes{ ... on Repository { nameWithOwner url description '
        'stargazerCount isArchived pushedAt primaryLanguage{name} } } } } } }'
    ) % json.dumps(list_id)

    items: list[dict] = []
    cursor = None
    while True:
        if cursor:
            paged_query = query.replace("$c", json.dumps(cursor))
        else:
            paged_query = (
                query.replace(", after:$c", "")
                .replace("query($c:String)", "query")
            )

        data = gq(paged_query)
        connection = (((data.get("data") or {}).get("node")) or {}).get("items")
        if connection is None:
            raise RuntimeError(f"GitHub returned no items connection for list {list_id}")

        for node in connection.get("nodes") or []:
            if node.get("nameWithOwner"):
                items.append(node)

        page_info = connection.get("pageInfo") or {}
        if page_info.get("hasNextPage"):
            cursor = page_info.get("endCursor")
            if not cursor:
                raise RuntimeError(
                    f"GitHub reported another page but no endCursor for list {list_id}"
                )
            time.sleep(0.25)
        else:
            break

    return items


def render_list(name: str, description: str, items: list[dict], snapshot: str) -> str:
    body = [
        f"# {name}",
        "",
        description,
        "",
        f"[← back to index](../README.md) · {len(items)} list memberships · snapshot {snapshot} UTC",
        "",
        "> Inclusion means the repository is in this research list; it is not an endorsement or quality ranking. Entries are sorted by GitHub star count for scanability.",
        "",
        "| Repo | ★ | Lang | Notes |",
        "|---|--:|---|---|",
    ]

    for item in items:
        archived = " `archived`" if item.get("isArchived") else ""
        language = (item.get("primaryLanguage") or {}).get("name") or ""
        description = (item.get("description") or "").replace("|", "\\|")[:140]
        body.append(
            f"| [{item['nameWithOwner']}]({item['url']}) | "
            f"{item.get('stargazerCount', 0)} | {language} | {description}{archived} |"
        )

    return "\n".join(body) + "\n"



def render_repo_view(title: str, description: str, rows: list[dict], snapshot: str,
                     extra_column: str = "", extra_value=None) -> str:
    headers = ["Repo", "★", "Lang", "Lists"]
    if extra_column:
        headers.append(extra_column)
    headers.append("Notes")
    body = [
        f"# {title}",
        "",
        description,
        "",
        f"[← back to index](../README.md) · snapshot {snapshot} UTC",
        "",
        "| " + " | ".join(headers) + " |",
        "|" + "|".join(["---", "--:", "---", "---"] + (["---"] if extra_column else []) + ["---"]) + "|",
    ]
    for row in rows:
        language = (row.get("primaryLanguage") or {}).get("name") or ""
        notes = (row.get("description") or "").replace("|", "\\|")[:120]
        list_names = ", ".join(sorted(row.get("lists") or []))
        cells = [
            f"[{row['nameWithOwner']}]({row['url']})",
            str(row.get("stargazerCount", 0)),
            language,
            list_names,
        ]
        if extra_column:
            value = extra_value(row) if extra_value else row.get(extra_column, "")
            cells.append(str(value))
        cells.append(notes + (" `archived`" if row.get("isArchived") else ""))
        body.append("| " + " | ".join(cells) + " |")
    return "\n".join(body) + "\n"


def build_repo_index(snapshots: list[dict]) -> dict[str, dict]:
    index: dict[str, dict] = {}
    for collection in snapshots:
        for item in collection["items"]:
            key = item["nameWithOwner"]
            record = index.setdefault(key, dict(item, lists=[]))
            if collection["name"] not in record["lists"]:
                record["lists"].append(collection["name"])
    return index


def load_previous_snapshot() -> dict:
    latest = SNAPSHOTS_DIR / "latest.json"
    if not latest.exists():
        return {}
    try:
        return json.loads(latest.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}


def main() -> None:
    data = gq(
        "{viewer{login lists(first:50){nodes{id name description isPrivate}}}}"
    )
    viewer = (data.get("data") or {}).get("viewer") or {}
    login = viewer.get("login")
    if not login:
        raise RuntimeError("GitHub returned no viewer login; refusing to overwrite the index")

    public_lists = [
        item
        for item in (viewer.get("lists") or {}).get("nodes", [])
        if not item.get("isPrivate")
    ]
    if not public_lists:
        raise RuntimeError(
            "GitHub returned zero public Lists; refusing to overwrite a non-empty index"
        )

    # Fetch everything before writing anything. A partial API outage therefore
    # cannot leave a half-regenerated working tree.
    snapshots = []
    unique_repositories: set[str] = set()
    membership_total = 0

    for github_list in public_lists:
        items = list_items(github_list["id"])
        items.sort(key=lambda repo: -(repo.get("stargazerCount") or 0))
        membership_total += len(items)
        unique_repositories.update(
            item["nameWithOwner"] for item in items if item.get("nameWithOwner")
        )
        snapshots.append(
            {
                "name": github_list["name"],
                "description": github_list.get("description") or "",
                "slug": slug(github_list["name"]),
                "items": items,
            }
        )
        sys.stderr.write(f"  {github_list['name']}: {len(items)}\n")

    snapshot = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    LISTS_DIR.mkdir(parents=True, exist_ok=True)
    VIEWS_DIR.mkdir(parents=True, exist_ok=True)
    SNAPSHOTS_DIR.mkdir(parents=True, exist_ok=True)

    repo_index = build_repo_index(snapshots)
    previous_snapshot = load_previous_snapshot()
    previous_repos = previous_snapshot.get("repositories") or {}

    expected_files = set()
    for item in snapshots:
        filename = f"{item['slug']}.md"
        expected_files.add(filename)
        (LISTS_DIR / filename).write_text(
            render_list(
                item["name"],
                item["description"],
                item["items"],
                snapshot,
            ),
            encoding="utf-8",
        )

    # A renamed/deleted GitHub List should not leave an orphaned public page.
    for existing in LISTS_DIR.glob("*.md"):
        if existing.name not in expected_files:
            existing.unlink()


    unique_rows = list(repo_index.values())

    recent = sorted(
        [row for row in unique_rows if row.get("pushedAt")],
        key=lambda row: row.get("pushedAt") or "",
        reverse=True,
    )[:100]
    (VIEWS_DIR / "recently-active.md").write_text(
        render_repo_view(
            "Recently active repositories",
            "The 100 most recently pushed repositories in the current research library. Recency is not a quality score.",
            recent,
            snapshot,
            "Last push",
            lambda row: (row.get("pushedAt") or "")[:10],
        ),
        encoding="utf-8",
    )

    archived = sorted(
        [row for row in unique_rows if row.get("isArchived")],
        key=lambda row: -(row.get("stargazerCount") or 0),
    )
    (VIEWS_DIR / "archived.md").write_text(
        render_repo_view(
            "Archived repositories",
            "Projects currently marked archived on GitHub. This is useful for pruning or finding maintained successors.",
            archived,
            snapshot,
        ),
        encoding="utf-8",
    )

    overlap = sorted(
        [row for row in unique_rows if len(row.get("lists") or []) >= 2],
        key=lambda row: (-len(row.get("lists") or []), -(row.get("stargazerCount") or 0)),
    )
    (VIEWS_DIR / "overlap.md").write_text(
        render_repo_view(
            "Cross-category overlap",
            "Repositories that appear in two or more curated Lists. High overlap often identifies infrastructure with cross-cutting relevance.",
            overlap,
            snapshot,
            "List count",
            lambda row: len(row.get("lists") or []),
        ),
        encoding="utf-8",
    )

    movers = []
    for row in unique_rows:
        previous = previous_repos.get(row["nameWithOwner"]) or {}
        old_stars = previous.get("stars")
        if isinstance(old_stars, int):
            delta = (row.get("stargazerCount") or 0) - old_stars
            if delta > 0:
                mover = dict(row)
                mover["star_delta"] = delta
                movers.append(mover)
    movers.sort(key=lambda row: (-row["star_delta"], -(row.get("stargazerCount") or 0)))
    (VIEWS_DIR / "movers.md").write_text(
        render_repo_view(
            "Observed star movers",
            "Largest positive star-count changes since the previous generated snapshot. This is observed repository momentum, not an endorsement.",
            movers[:100],
            snapshot,
            "Δ stars",
            lambda row: f"+{row['star_delta']}",
        ),
        encoding="utf-8",
    )

    snapshot_payload = {
        "snapshot": snapshot,
        "repositories": {
            name: {
                "stars": row.get("stargazerCount") or 0,
                "pushed_at": row.get("pushedAt"),
                "archived": bool(row.get("isArchived")),
                "lists": sorted(row.get("lists") or []),
            }
            for name, row in sorted(repo_index.items())
        },
    }
    snapshot_json = json.dumps(snapshot_payload, indent=2, sort_keys=True) + "\n"
    (SNAPSHOTS_DIR / "latest.json").write_text(snapshot_json, encoding="utf-8")
    history_file = SNAPSHOTS_DIR / f"{snapshot}.json"
    history_file.write_text(snapshot_json, encoding="utf-8")


    rows = sorted(snapshots, key=lambda item: -len(item["items"]))
    index = [
        f"# ★ {login}'s research library",
        "",
        f"A curated snapshot of **{membership_total} list memberships** across "
        f"**{len(public_lists)} public GitHub Lists**, representing "
        f"**{len(unique_repositories)} unique repositories**.",
        "",
        f"**Snapshot:** `{snapshot}` UTC · "
        f"Generated from manually curated GitHub Lists by "
        f"[`scripts/generate.py`](scripts/generate.py).",
        "",
        "## How to read this",
        "",
        "This is a working research library, not a recommendation engine or ranking.",
        "",
        "- **Selection is manual.** I decide which repositories belong in each GitHub List.",
        "- **Rendering is automatic.** The generator fetches public list membership and repository metadata, then writes this index.",
        "- **Ordering is mechanical.** Entries are sorted by GitHub star count within each list for scanability; stars are not treated as a quality score.",
        "- **Metadata is point-in-time.** Star counts, descriptions, language, and archive state reflect the snapshot date above.",
        "- **Overlap is expected.** A repository can belong to more than one list, so membership count and unique-repository count are reported separately.",
        "- **Inclusion is not endorsement.** Lists include tools I am evaluating, comparing, monitoring, or may want to revisit.",
        "",
        f"Maintained by [Rich Berman](https://github.com/{login}) / "
        "[MHSB Solutions](https://github.com/MHSBai) · "
        "[granolacowboy.dev](https://granolacowboy.dev)",
        "",
        "## Research views",
        "",
        "- [Recently active](views/recently-active.md) — repositories ordered by most recent push.",
        "- [Observed star movers](views/movers.md) — star-count changes since the previous generated snapshot.",
        "- [Cross-category overlap](views/overlap.md) — repositories present in two or more curated Lists.",
        "- [Archived repositories](views/archived.md) — candidates for pruning or successor research.",
        "",
        "The mover view is intentionally based on this repository's own saved snapshots; it does not infer growth from a single current star count.",
        "",
        "## Browse by topic",
        "",
        "| List | Count | About |",
        "|---|--:|---|",
    ]

    for item in rows:
        description = item["description"].replace("|", "\\|")
        index.append(
            f"| [{item['name']}](lists/{item['slug']}.md) | "
            f"{len(item['items'])} | {description} |"
        )

    index += [
        "",
        "## Regeneration",
        "",
        "The generator is read-only against the GitHub API. With the GitHub CLI authenticated as the account whose Lists you want to render:",
        "",
        "```bash",
        "python scripts/generate.py",
        "```",
        "",
        f"<sub>Snapshot {snapshot} UTC · {membership_total} list memberships · "
        f"{len(unique_repositories)} unique repositories · {len(public_lists)} lists.</sub>",
    ]

    (OUT / "README.md").write_text("\n".join(index) + "\n", encoding="utf-8")
    print(
        json.dumps(
            {
                "lists": len(public_lists),
                "list_memberships": membership_total,
                "unique_repositories": len(unique_repositories),
                "snapshot": snapshot,
                "views": 4,
                "out": str(OUT),
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
