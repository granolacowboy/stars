#!/usr/bin/env python3
"""Generate a categorized 'awesome-stars' index from the user's GitHub Lists.

Reads viewer.lists (skips private lists), writes a multi-file index:
  build/README.md          index TOC (list, count, description) + totals
  build/lists/<slug>.md     per-list table (repo, stars, lang, archived, description)
100% read-only against the API; output is committed to granolacowboy/stars.
"""
from __future__ import annotations
import json, subprocess, sys, time, re
from pathlib import Path
OUT = Path(__file__).resolve().parents[1]


def gq(q):
    for _ in range(8):
        p = subprocess.run(["gh", "api", "graphql", "-f", f"query={q}"], text=True, capture_output=True)
        if p.returncode == 0:
            try:
                return json.loads(p.stdout)
            except Exception:
                pass
        time.sleep(6)
    return {}


def slug(s):
    return re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-")


def list_items(list_id):
    q = ('query($c:String){ node(id:%s){ ... on UserList { items(first:100, after:$c){ '
         'pageInfo{hasNextPage endCursor} nodes{ ... on Repository { nameWithOwner url description '
         'stargazerCount isArchived primaryLanguage{name} } } } } } }') % json.dumps(list_id)
    out, cur = [], None
    while True:
        qq = q.replace("$c", json.dumps(cur)) if cur else q.replace(", after:$c", "").replace("query($c:String)", "query")
        d = gq(qq)
        conn = (((d.get("data") or {}).get("node")) or {}).get("items") or {}
        for n in conn.get("nodes") or []:
            if n.get("nameWithOwner"):
                out.append(n)
        pi = conn.get("pageInfo") or {}
        if pi.get("hasNextPage"):
            cur = pi["endCursor"]; time.sleep(0.25)
        else:
            break
    return out


def main():
    (OUT / "lists").mkdir(parents=True, exist_ok=True)
    d = gq('{viewer{login lists(first:50){nodes{id name description isPrivate}}}}')
    v = (d.get("data") or {}).get("viewer") or {}
    login = v.get("login", "granolacowboy")
    lists = [L for L in (v.get("lists") or {}).get("nodes", []) if not L.get("isPrivate")]
    rows = []; total = 0
    for L in lists:
        items = list_items(L["id"])
        items.sort(key=lambda r: -(r.get("stargazerCount") or 0))
        total += len(items)
        sg = slug(L["name"])
        body = [f"# {L['name']}", "", (L.get("description") or ""), "",
                f"[← back to index](../README.md) · {len(items)} repos", "",
                "| Repo | ★ | Lang | Notes |", "|---|--:|---|---|"]
        for r in items:
            arch = " `archived`" if r.get("isArchived") else ""
            lang = (r.get("primaryLanguage") or {}).get("name") or ""
            desc = (r.get("description") or "").replace("|", "\\|")[:140]
            body.append(f"| [{r['nameWithOwner']}]({r['url']}) | {r.get('stargazerCount',0)} | {lang} | {desc}{arch} |")
        (OUT / "lists" / f"{sg}.md").write_text("\n".join(body) + "\n")
        rows.append((L["name"], sg, len(items), L.get("description") or ""))
        sys.stderr.write(f"  {L['name']}: {len(items)}\n")
    rows.sort(key=lambda x: -x[2])
    idx = [f"# ★ {login}'s starred library",
           "",
           f"A curated, auto-generated index of **{total}** starred repositories across **{len(lists)}** lists. "
           "Generated from GitHub Lists; refreshed weekly.",
           "",
           f"Maintained by [Rich Berman](https://github.com/{login}) / [MHSB Solutions](https://github.com/MHSBai) · [granolacowboy.dev](https://granolacowboy.dev)",
           "", "| List | Count | About |", "|---|--:|---|"]
    for name, sg, n, desc in rows:
        idx.append(f"| [{name}](lists/{sg}.md) | {n} | {desc.replace('|','\\|')} |")
    idx += ["", f"<sub>Total: {total} repositories · {len(lists)} lists · generated automatically.</sub>"]
    (OUT / "README.md").write_text("\n".join(idx) + "\n")
    print(json.dumps({"lists": len(lists), "total_repos": total, "out": str(OUT)}, indent=2))


if __name__ == "__main__":
    main()
